# Histórico del Proyecto KB - Solutions Portal

## Resumen del Proyecto
Portal público de base de conocimiento construido en Django, que consume la API de
**ServiceDesk Plus Cloud** para publicar soluciones a usuarios no autenticados.

---

## Sesión: 2026-02-19

### Contexto General
- El cliente usa **ServiceDesk Plus Cloud** y su módulo de Soluciones.
- Las soluciones son solo accesibles a usuarios **autenticados** dentro de SDP Cloud.
- Se necesita exponer ciertas soluciones al **público general** sin autenticación.
- Django actúa como intermediario: consume la API de SDP con credenciales en el servidor
  y sirve el contenido al mundo sin exponer las claves.

### Arquitectura Definida
```
SDP Cloud API  →  Django (kb)  →  Portal HTML (público)
```

### Configuración del Entorno
- **Python**: entorno virtual en `venv/`
- **Django 6.0.2** instalado
- **Proyecto Django**: `kb/` (Opción B - carpeta separada)
- **App**: `portal` (vistas y URLs del portal público)
- **Recursos**: `resources/` (paquete con lógica reutilizable)

### Archivos Clave (Actualizados)
| Archivo | Propósito |
|---|---|
| `kb/portal/views.py` | Vista `home` → sirve `solutionsportal.html` |
| `kb/portal/urls.py` | URL `/home/` mapeada a la vista `home` |
| `kb/resources/token/sdp_auth.py` | Manejo de OAuth tokens (refresh automático) |
| `kb/resources/token/token_store.json` | Almacén local de tokens (gitignored) |
| `kb/resources/solutions/sdp_solutions.py` | API Client para el módulo de Soluciones SDP |
| `kb/resources/utils.py` | Funciones utilitarias generales |
| `kb/.env` | Credenciales OAuth y URL base (gitignored) |

### Decisiones Técnicas
- Funciones organizadas como **métodos estáticos** (`@staticmethod`) dentro de clases.
- Los tokens OAuth se almacenan en `token_store.json` (local, fuera del repo).
- El `refresh_token` puede venir de variable de entorno `SDP_REFRESH_TOKEN`.
- SDP Cloud usa **Zoho OAuth 2.0** para la autenticación API.
- Cada dominio funcional tiene su propio subdirectorio en `resources/` (`token/`, `solutions/`).

---

## Implementación: OAuth + SDP Solutions API (2026-02-19)

### `resources/token/sdp_auth.py` — OAuth Manager
| Método | Descripción |
|---|---|
| `get_access_token(client_id, secret)` | Punto de entrada. Devuelve token válido |
| `refresh_access_token(...)` | Llama a Zoho y obtiene nuevo access_token |
| `save_tokens(data)` | Persiste tokens en `token_store.json` |
| `load_tokens()` | Lee tokens almacenados localmente |

### `resources/solutions/sdp_solutions.py` — SDP API Client
Replica exacta de los calls de Postman.

| Método | Descripción |
|---|---|
| `get_all(token, start_index=0, row_count=1000)` | Un lote de soluciones |
| `get_all_paginated(token)` | Pagina automáticamente, retorna TODAS |
| `get_by_id(token, solution_id)` | Detalle de una solución |

**Headers (idénticos a Postman):**
- `Authorization: Zoho-oauthtoken {token}`
- `Accept: application/vnd.manageengine.sdp.v3+json`
- `Content-Type: application/x-www-form-urlencoded`

**Paginación:**
- `start_index: 0` → primeras 1000
- `start_index: 1000` → siguientes 1000
- Se detiene automáticamente cuando llegan menos de `row_count`

### Prueba Exitosa
```
SUCCESS - 10 soluciones retornadas
Primera: OpManager reset admin password (SOL-21)
```

### Pendiente
- [x] Credenciales OAuth configuradas en `.env`
- [x] Implementar `sdp_auth.py` con refresh automático
- [x] Implementar `sdp_solutions.py` con paginación
- [x] Push inicial a GitHub
- [ ] Crear endpoint Django `/api/solutions/`
- [ ] Conectar frontend JS con datos reales del API
- [ ] Definir filtro de soluciones "públicas" en SDP
