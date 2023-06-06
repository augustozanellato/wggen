class ConfigSection:
    def __init__(self, name: str, values: dict[str, int | str], comment: str | None = None):
        self.name = name
        self.values = values
        self.comment = comment

    def dumps(self) -> str:
        headers = f"[{self.name}]\n"
        comment = f"# {self.comment}\n" if self.comment else ""
        content = "\n".join(f"{k} = {v}" for k, v in self.values.items())
        return headers + comment + content


class WGConfig:
    def __init__(self):
        self.sections: list[ConfigSection] = []
        self.others: dict[str, str | int] = {}

    def add_section(self, section: ConfigSection) -> None:
        self.sections.append(section)

    def add_value(self, key: str, value: str | int) -> None:
        self.others[key] = value

    def dumps(self) -> str:
        sections = "\n\n".join(s.dumps() for s in self.sections)
        values = "\n".join(f"{k} = {v}" for k, v in self.others.items())
        return sections + "\n\n" + values + "\n"
