# Repositorio código prácticas CAHA 2022
Código para trabajar y procesar los datos de la práctica observacional 2022 del observatorio Calar Alto, así como para realizar ajustes de curvas de luz con phoebe.

# Requisitos
- python >= 3.6
  + astropy
  + ccdproc
  + photutils
  + numpy
  + pandas
  + matplotlib
- R >= 4.0
  + data.table
  + magrittr
  
 # Estructura del projecto

```
../
├── data/
├── src/
└── output/
```

- `data/` Carpeta que contiene todos las imágenes fits "en crudo" sin procesar y otros
datos necesarios como tablas con coordenadas y magnitudes estándares.
- `src/` Carpeta que contiene todos los scripts de código utilizados.
- `output/` Carpeta que contiene todos las imágenes fits procesadas, así como cualquier otro dato o gráfico producido mediante código a partir de los datos en `data/`

Para que el código funcione, basta guardar los datos proporcionados por el técnico
de Calar Alto en la carpeta `data/`, dentro de la subcarpetas `20221104/`,
`20221105/` y `20221106/` y ejecutar los scripts que aparecen en `src/scripts/` en orden.
