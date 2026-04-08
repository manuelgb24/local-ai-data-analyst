# PRODUCT_SCOPE

## Propósito
Fijar qué entra y qué no entra en la fase actual del producto para evitar que el proyecto reabra alcance accidentalmente.

## Qué entra en la fase producto actual
### Núcleo funcional
- un único agente real: `data_analyst`;
- selección explícita del agente;
- un dataset principal por run;
- entrada por ruta manual local (`csv`, `xlsx`, `parquet`);
- DuckDB local;
- Ollama local;
- artifacts trazables por run.

### Superficie de producto prevista
- interfaz web principal;
- API local;
- CLI operativa;
- health/readiness operativos;
- historial persistente local de runs y artifacts;
- observabilidad mínima;
- packaging y release hardening.

## Qué sigue fuera de alcance
- Planner;
- routing automático;
- multi-agent real;
- multi-dataset por run;
- auth;
- multiusuario;
- backend hosted;
- colas, workers remotos o infraestructura distribuida;
- RAG;
- catálogo complejo de datasets.

## Qué sí puede crecer sin reabrir alcance
- experiencia de uso;
- operación local;
- health y readiness;
- trazabilidad;
- observabilidad;
- historial persistente local;
- forma de distribución local;
- validación automatizada;
- calidad de la UI y de la API local.

## Qué requeriría una decisión nueva formal
- más agentes reales;
- selección automática de agente;
- ejecución remota;
- varios datasets por run;
- cuentas de usuario;
- permisos o colaboración multiusuario;
- soporte multi-modelo o multi-proveedor.

## Regla práctica
Si un cambio modifica la experiencia de producto sin tocar el núcleo funcional congelado, probablemente entra.

Si un cambio altera el alcance funcional, la topología del sistema o el modelo operativo local-first, necesita decisión nueva y documentación explícita.
