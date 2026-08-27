## 1. Remover código y documentación huérfanos

- [x] 1.1 Eliminar `src/framework/reannotate.py` (`git rm`).
- [x] 1.2 Eliminar `docs/reannotate_explore.md` (`git rm`).

## 2. Verificación

- [x] 2.1 Confirmar que `tests/conftest.py` y `tests/test_smoke.py` no
      importan `framework.reannotate` (ya verificado en la exploración,
      re-chequear tras el borrado).
- [x] 2.2 Confirmar que `pyproject.toml` no declara ningún entry point o
      script que referencie `framework.reannotate`.
- [x] 2.3 Grep de `reannotate` sobre el repo completo (excluyendo
      `openspec/changes/archive/`) para confirmar cero referencias vivas
      fuera de los changes archivados, que se conservan como historial.

## 3. Ejecución bloqueante — entrega al QA

- [x] 3.1 Entregar al QA las instrucciones de verificación:
      `pytest --collect-only` (confirma que la suite sigue coleccionando
      sin errores de import) y `ruff check .` (confirma que no quedan
      referencias rotas). Este change no agrega ni modifica tests, así que
      no hay un `pytest -k` específico que correr — solo confirmar que
      nada se rompió.
- [x] 3.2 Esperar retroalimentación explícita del QA antes de proceder a
      `/opsx:archive`.
