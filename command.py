class Command:
    # _function: Callable[Any, dict]

    def __init__(self, name: str, command_aliases: list, description: str, func:callable):
        self._name = name
        self._aliases = command_aliases
        self._description = description
        self._function = func

    def get_name(self):
        return self._name

    def get_aliases(self):
        return self._aliases

    def get_description(self):
        return self._description

    def get_help(self):
        return "\n\n**%s** - %s\n__Aliases:__ *%s*" % (self.get_name(), self.get_description(),
                                                       '*, *'.join(alias for alias in self.get_aliases()))

    def run(self, *args) -> dict:
        return self._function(*args)