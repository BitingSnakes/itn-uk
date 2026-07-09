import pynini
from pynini.lib import pynutil

from ukr.graph_utils import GraphFst, delete_extra_space, delete_space
from ukr.taggers.address import AddressFst
from ukr.taggers.cardinal import CardinalFst
from ukr.taggers.century import CenturyFst
from ukr.taggers.code import CodeFst
from ukr.taggers.date import DateFst
from ukr.taggers.decade import DecadeFst
from ukr.taggers.decimal import DecimalFst
from ukr.taggers.duration import DurationFst
from ukr.taggers.electronic import ElectronicFst
from ukr.taggers.fraction import FractionFst
from ukr.taggers.ip import IpFst
from ukr.taggers.legal import LegalFst
from ukr.taggers.measure import MeasureFst
from ukr.taggers.money import MoneyFst
from ukr.taggers.number_sign import NumberSignFst
from ukr.taggers.ordinal import OrdinalFst
from ukr.taggers.range import RangeFst
from ukr.taggers.score import ScoreFst
from ukr.taggers.telephone import TelephoneFst
from ukr.taggers.time import TimeFst
from ukr.taggers.version import VersionFst
from ukr.taggers.word import WordFst


class ClassifyFst(GraphFst):

    def __init__(self):
        super().__init__(name="tokenize_and_classify", kind="classify")

        cardinal = CardinalFst()
        cardinal_graph = cardinal.fst

        ordinal = OrdinalFst(cardinal)
        ordinal_graph = ordinal.fst

        decimal = DecimalFst(cardinal)
        decimal_graph = decimal.fst

        fraction_graph = FractionFst(cardinal=cardinal).fst
        measure_graph = MeasureFst(cardinal=cardinal, decimal=decimal).fst
        date_graph = DateFst(cardinal=cardinal, ordinal=ordinal).fst
        time_graph = TimeFst(cardinal=cardinal, ordinal=ordinal).fst
        telephone_graph = TelephoneFst(cardinal=cardinal).fst
        electronic_graph = ElectronicFst(cardinal=cardinal).fst
        century_graph = CenturyFst(cardinal=cardinal).fst
        number_sign_graph = NumberSignFst(cardinal=cardinal).fst
        range_graph = RangeFst(cardinal=cardinal).fst
        code_graph = CodeFst(cardinal=cardinal).fst
        address_graph = AddressFst(cardinal=cardinal).fst
        duration_graph = DurationFst(cardinal=cardinal).fst
        decade_graph = DecadeFst().fst
        legal_graph = LegalFst(cardinal=cardinal).fst
        score_graph = ScoreFst(cardinal=cardinal).fst
        version_graph = VersionFst(cardinal=cardinal).fst
        ip_graph = IpFst(cardinal=cardinal).fst
        word_graph = WordFst().fst
        money_graph = MoneyFst(cardinal=cardinal, decimal=decimal).fst

        classify = (
                pynutil.add_weight(duration_graph, 1.09)
                | pynutil.add_weight(decade_graph, 1.09)
                | pynutil.add_weight(legal_graph, 1.09)
                | pynutil.add_weight(score_graph, 1.09)
                | pynutil.add_weight(version_graph, 1.09)
                | pynutil.add_weight(ip_graph, 1.09)
                | pynutil.add_weight(electronic_graph, 1.09)
                | pynutil.add_weight(address_graph, 1.09)
                | pynutil.add_weight(range_graph, 1.09)
                | pynutil.add_weight(century_graph, 1.09)
                | pynutil.add_weight(number_sign_graph, 1.09)
                | pynutil.add_weight(code_graph, 1.09)
                | pynutil.add_weight(telephone_graph, 1.09)
                | pynutil.add_weight(decimal_graph, 1.1)
                | pynutil.add_weight(fraction_graph, 1.1)
                | pynutil.add_weight(measure_graph, 1.1)
                | pynutil.add_weight(cardinal_graph, 1.1)
                | pynutil.add_weight(ordinal_graph, 1.1)
                | pynutil.add_weight(money_graph, 1.1)
                | pynutil.add_weight(date_graph, 1.1)
                | pynutil.add_weight(time_graph, 1.1)
                | pynutil.add_weight(word_graph, 100)
        )

        token = pynutil.insert("tokens { ") + classify + pynutil.insert(" }")

        graph = token + pynini.closure(delete_extra_space + token)
        graph = delete_space + graph + delete_space

        self.fst = graph.optimize()
