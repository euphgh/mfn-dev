from dataclasses import dataclass
from typing import Any


@dataclass()
class AbstractRepeater:
    container: str
    clock: str
    instance: str
    cell_num: int
    interconnection: str

    @classmethod
    def fromJson(cls, container: str, clock: str, json: dict[str, Any]):
        container = container
        clock = clock
        instance = json["name"]
        cell_num = json["pd"]
        interconnection = json["interconnection"]
        return cls(container, clock, instance, cell_num, interconnection)

    def match(self) -> list[tuple[str, str]]:
        raise NotImplementedError()


def repJsonParser(
    repCls: type[AbstractRepeater],
    json: dict[str, dict[str, list[dict[str, Any]]]],
):
    res = list[repCls]()
    total_rep_nr = 0
    for container_field in json.items():
        container = container_field[0]
        clock_dict = container_field[1]
        for clock_field in clock_dict.items():
            clock = clock_field[0]
            rep_array = clock_field[1]
            total_rep_nr = total_rep_nr + rep_array.__len__()
            for rep_json in rep_array:
                rep_obj = repCls.fromJson(container, clock, rep_json)
                # try:
                #     rep_obj = repCls.fromJson(container, clock, rep_json)
                # except Exception as e:
                #     print(f"Fail to load {json}: {e}")
                #     continue
                res.append(rep_obj)
    print(f"load {res.__len__()} valid {repCls.__name__} in total {total_rep_nr}")
    return res
