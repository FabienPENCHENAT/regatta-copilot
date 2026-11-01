from sailrouter.ensemble.option_outlook import OptionOutlook


def test_gains_are_measured_against_the_recommended_option_in_each_weather():
    outlook = [
        {"a": {48.0: 100.0}, "b": {48.0: 110.0}, "c": {48.0: 90.0}},   # recommended
        {"a": {48.0: 95.0}, "b": {48.0: 130.0}, "c": {48.0: 80.0}},    # ahead in a and c, far behind in b
    ]
    recommended, other = OptionOutlook().summarize(outlook)
    assert recommended == [{"hours": 48, "to_go_nm": 100, "gain_nm": 0.0, "worst_nm": 0.0, "ahead_share": 0.0}]
    assert other == [{"hours": 48, "to_go_nm": 102, "gain_nm": -1.7, "worst_nm": -20.0, "ahead_share": 0.67}]
