# Mission Intent Repair

[Français](README.md) · [English](README.en.md)

**Desaparece un enlace. ¿Qué plan conserva más valor sin reescribir el pasado?**

Laboratorio ejecutable de reparación de misiones con el verdadero solucionador OR-Tools CP-SAT, interfaz local y comprobador independiente. Interrumpe el relé principal: el plan utiliza el de respaldo, conserva las dos tareas iniciadas y comprueba energía y almacenamiento en cada paso.

![Demostración sintética: reparación tras perder un relé](docs/preview-fr.png)

## Probar

Python 3.11 o posterior; sin clave ni servicio remoto.

```sh
python3 -m venv .venv
.venv/bin/pip install .
.venv/bin/python -m mission_repair serve --lang es
```

Abrir `http://127.0.0.1:8764/?lang=es`. Escenario, parámetros, plan y pruebas JSON permanecen locales. La misma interfaz admite FR/EN/ES.

```sh
.venv/bin/python -m mission_repair demo --lang es
.venv/bin/python -m mission_repair repair mission_repair/examples/lunar-relay.json
.venv/bin/python -m mission_repair check caso.json plan.json
```

`check` acepta `{ "task-id": start_tick }` o un informe con `plan`. Los códigos de error son estables; `--lang` localiza los mensajes.

## Cálculos

- Ventanas de inicio y fin, duraciones enteras, dependencias y canales exclusivos.
- Batería con generación solar, consumo base y tareas; almacenamiento con producción y descarga al terminar la tarea.
- Pasado fijo: una tarea cuyo inicio anterior precede a `freeze_before` conserva exactamente su inicio, incluidas las tareas en curso.
- Objetivo lexicográfico: maximizar la utilidad declarada, minimizar las tareas modificadas y después el desplazamiento temporal. El coeficiente 3000 supera el desplazamiento total posible dentro de los límites admitidos.
- Reproducción independiente de ventanas, obligaciones, dependencias, colisiones, batería y almacenamiento, sin variables del solucionador.
- SHA-256 de las hipótesis, cambios explícitos y exportación JSON reproducible.

La interrupción sintética suministrada produce **8 unidades de utilidad declarada frente a 10 antes del fallo**, con **dos tareas modificadas**. Son valores del escenario, no rendimiento espacial medido. El plan antiguo queda invalidado tras el fallo.

`OPTIMAL` demuestra los tres niveles del objetivo en el modelo. `FEASIBLE` indica un plan comprobado sin prueba completa de optimalidad. `INFEASIBLE` indica una contradicción; `required_conflict` es un conjunto suficiente de obligaciones incompatibles, **no necesariamente mínimo**. `UNKNOWN` conserva la ausencia de resultado.

## Modelo y límites

Hasta 30 tareas y 96 pasos; energía y datos son enteros arbitrarios. Generación y consumo se agregan por paso; los cambios simultáneos de almacenamiento se agregan en la frontera. Una capacidad reducida afecta a todo el horizonte: para un fallo a una hora concreta, proporcionar un horizonte nuevo y su estado inicial, en vez de modificar retroactivamente el pasado.

No calcula órbitas, actitud ni geometría de visibilidad; el usuario proporciona las ventanas. No conecta hardware, simuladores de vuelo ni software embarcado. Los resultados no califican una misión real. El tiempo de cálculo es limitado y las pruebas solo cubren las hipótesis suministradas. El servidor escucha en la interfaz local y no expone comandos de vuelo.

## Comparación

[PlanDev](https://nasa-ammos.github.io/plandev-docs/introduction/) ya proporciona modelado, planificación y restricciones de misiones. [OR-Tools](https://developers.google.com/optimization/scheduling/job_shop) ya resuelve calendarios. Este repositorio reutiliza CP-SAT para una demostración pequeña y autónoma: **fallo → pasado fijo → reparación óptima acotada → reproducción independiente**. No afirma superioridad general.

[Mission Benchmark Commons](https://github.com/gbesse/mission-benchmark-commons) compara motores orbitales y [Contact Market](https://github.com/gbesse/contact-market) optimiza contactos. Aquí se reparan calendarios y recursos después de un fallo; no se copian esos repositorios.

## Verificación

```sh
.venv/bin/python -m unittest discover -s tests -v
npm ci
npx playwright install chromium
PYTHON=.venv/bin/python npm run test:browser
npm run format:check
```

Incluye comparación exhaustiva de problemas pequeños, fallos, obligaciones imposibles, recursos agotados, pasado fijo y exportaciones de navegador en los tres idiomas. La CI instala también una rueda Python fuera del código fuente. Licencia MIT; alfa de investigación.
