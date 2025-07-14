"""
core/__init__.py

Este paquete reúne las utilidades centrales para la extracción y normalización
de datos de comparendos.

Exporta:
  - id_key(raw: str) -> str
      Genera una clave numérica única a partir de un identificador bruto,
      eliminando letras iniciales y acentos.

  - norm(text: str) -> str
      Normaliza textos (p. ej. encabezados) eliminando acentos y espacios,
      convirtiendo a minúsculas.

  - run_extract(txt_path: pathlib.Path) -> tuple[pd.DataFrame, pd.DataFrame]
      Lee un archivo de texto con bloques de comparendos, aplica parsers
      dinámicos y devuelve dos DataFrames: 
        1) detalle con entradas individuales 
        2) resumen agrupado por clave.

  - PARSERS: dict[str, Callable]
      Diccionario mapeando cada sección reconocida al parser correspondiente,
      descubierto automáticamente en el paquete `parsers`.
"""


from .clean import id_key, norm
from .manager import run_extract, PARSERS