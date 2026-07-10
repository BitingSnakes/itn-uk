import pynini
from pynini.lib import pynutil

from ukr.graph_utils import (
    NEMO_CHAR,
    NEMO_DIGIT,
    GraphFst,
    delete_extra_space,
    delete_space,
)
from ukr.taggers.cardinal import CardinalFst
from ukr.taggers.ordinal import OrdinalFst
from ukr.utils import get_abs_path


class TimeFst(GraphFst):
    """
    Finite state transducer for classifying time
        e.g. сьома година п'ять хвилин" -> time { hours: "07" minutes: "05" }
        e.g. о пів на десяту -> time { hours: "09" minutes: "30" }
        e.g. чверть на десяту -> time { hours: "09" minutes: "15" }
        e.g. за чверть одинадцята -> time { hours: "10" minutes: "45" }
        e.g. п'ять хвилин на дванадцяту -> time { hours: "11" minutes: "05" }

        e.g. twelve past one -> time { minutes: "12" hours: "1" }
        e.g. two o clock a m -> time { hours: "2" suffix: "a.m." }
        e.g. quarter past two -> time { hours: "2" minutes: "15" }
    """

    def __init__(self, cardinal: CardinalFst, ordinal: OrdinalFst):
        super().__init__(name="time", kind="classify")

        hours = pynini.string_file(get_abs_path("data/time/hours.tsv"))
        minutes = pynini.string_file(get_abs_path("data/time/minutes.tsv"))
        to_hour = pynini.string_file(get_abs_path("data/time/to_hour.tsv"))
        zeros = cardinal.graph_zero

        hours_ordinal = ordinal.graph_up_to_hundred_component
        hours_ordinal = hours_ordinal @ (pynini.closure(NEMO_DIGIT) + pynutil.delete(pynini.union("-") + pynini.closure(NEMO_CHAR)))
        # Ordinal tables emit zero-padded hours.  The 24th hour is valid in
        # relative phrases such as "пів на двадцять четверту" (23:30), but
        # not as the hour component of an ordinary HH:MM clock value.
        hours_ordinal = hours_ordinal @ pynini.union(*(f"{value:02d}" for value in range(1, 25)))
        clock_hours = hours_ordinal @ pynini.union(*(f"{value:02d}" for value in range(1, 24)))

        graph_hours = clock_hours + delete_space + pynini.closure(pynutil.delete(hours), 0, 1)
        graph_hours = pynutil.insert("hours: \"") + graph_hours + pynutil.insert("\"")

        minutes_cardinal = cardinal.graph_up_to_hundred_component @ pynini.union(*(f"{value:02d}" for value in range(60)))
        minutes_cardinal += delete_space + pynini.closure(pynutil.delete(minutes), 0, 1)
        graph_minutes = pynutil.insert("minutes: \"") + minutes_cardinal + pynutil.insert("\"")

        graph_half_hour = pynini.closure(pynutil.delete("о "), 0, 1) + pynutil.delete("пів на ") + hours_ordinal
        graph_half_hour = graph_half_hour @ to_hour.invert()
        graph_half_hour = pynutil.insert("hours: \"") + graph_half_hour + pynutil.insert("\" minutes: \"30\"")

        to_hour_graph = hours_ordinal @ to_hour
        graph_to_quarter_hour = pynutil.delete("чверть на ") + to_hour_graph
        graph_to_quarter_hour = pynutil.insert("hours: \"") + graph_to_quarter_hour + pynutil.insert("\" minutes: \"15\"")

        graph_from_quarter_hour = pynutil.delete("за чверть ") + to_hour_graph
        graph_from_quarter_hour = pynutil.insert("hours: \"") + graph_from_quarter_hour + pynutil.insert("\" minutes: \"45\"")

        graph_hm = graph_hours + delete_extra_space + graph_minutes

        # NOTE: we use here special notation >> which will be processed after FST
        # The >> means move the current token to one position to right.

        # п'ять хвилин на дванадцяту -> time { hours: "11" minutes: "05" }
        graph_mh = graph_minutes + pynutil.insert(">>") + pynutil.delete(" на ") + pynutil.insert(" hours: \"") + to_hour_graph + pynutil.insert("\"")

        # дванадцята нуль нуль ->  time { hours: "12" minutes: "00" }
        graph_hzz = graph_hours + delete_space
        graph_hzz += pynini.union(
            pynutil.insert(" minutes: \"") + zeros + delete_space + zeros + pynutil.insert("\""),
            pynutil.insert(" minutes: \"") + zeros + delete_space + cardinal.graph_digit + pynutil.insert("\""),
        )

        # English-style structured day-period support, rendered as an
        # unambiguous 24-hour value ("третя година дня" -> 15:00).
        pm_hours = clock_hours @ pynini.string_map(
            [(f"{hour:02d}", f"{hour + 12:02d}") for hour in range(1, 12)] + [("12", "12")]
        )
        am_hours = clock_hours @ pynini.string_map(
            [(f"{hour:02d}", f"{hour:02d}") for hour in range(1, 12)] + [("12", "00")]
        )
        optional_hour_unit = pynini.closure(delete_space + pynutil.delete(hours), 0, 1)
        graph_period = pynini.union(
            pm_hours + optional_hour_unit + delete_space + pynutil.delete(pynini.union("дня", "вечора")),
            am_hours + optional_hour_unit + delete_space + pynutil.delete(pynini.union("ночі", "ранку")),
        )
        graph_period = pynutil.insert('hours: "') + graph_period + pynutil.insert('" minutes: "00"')

        time_zone = pynini.string_map(
            [
                ("за київським часом", "Europe/Kyiv"),
                ("за лондонським часом", "Europe/London"),
                ("за всесвітнім координованим часом", "UTC"),
            ]
        )
        optional_zone = pynini.closure(
            delete_extra_space + pynutil.insert('zone: "') + time_zone + pynutil.insert('"'), 0, 1
        )

        final_graph = graph_hm | graph_mh | graph_half_hour | graph_to_quarter_hour | graph_from_quarter_hour | graph_hzz | graph_period
        final_graph += optional_zone
        final_graph = self.add_tokens(final_graph.optimize())

        self.fst = final_graph.optimize()
