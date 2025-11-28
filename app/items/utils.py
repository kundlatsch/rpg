class SafeStats:
    """
    Wrapper seguro para acessar JSON de stats.
    Retorna um SafeStats vazio quando o campo não existe,
    permitindo acesso profundo sem quebras.
    """

    def __init__(self, data=None):
        self._data = data or {}

    def __getattr__(self, name):
        value = self._data.get(name)

        # valor existe
        if isinstance(value, dict):
            return SafeStats(value)
        if value is not None:
            return value

        # valor não existe → retorna SafeStats vazio
        return SafeStats()

    def __getitem__(self, key):
        value = self._data.get(key)

        if isinstance(value, dict):
            return SafeStats(value)
        if value is not None:
            return value

        return SafeStats()

    def get(self, key, default=None):
        value = self._data.get(key, default)

        if isinstance(value, dict):
            return SafeStats(value)
        if value is not None:
            return value

        return SafeStats()

    def to_dict(self):
        return self._data
    
    def __str__(self):
        return str(self.to_dict())
