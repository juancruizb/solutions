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

### Archivos Clave
| Archivo | Propósito |
|---|---|
| `kb/portal/views.py` | Vista `home` → sirve `solutionsportal.html` |
| `kb/portal/urls.py` | URL `/home/` mapeada a la vista `home` |
| `kb/resources/sdp_auth.py` | Manejo de OAuth tokens (refresh automático) |
| `kb/resources/utils.py` | Funciones utilitarias generales |
| `kb/resources/token_store.json` | Almacén local de tokens (no commitear) |

### Decisiones Técnicas
- Funciones organizadas como **métodos estáticos** (`@staticmethod`) dentro de clases.
- Los tokens OAuth se almacenan en `token_store.json` (local, fuera del repo).
- El `refresh_token` puede venir de variable de entorno `SDP_REFRESH_TOKEN`.
- SDP Cloud usa **Zoho OAuth 2.0** para la autenticación API.

### Pendiente
- [ ] Obtener `client_id`, `client_secret` y `refresh_token` iniciales del cliente.
- [ ] Implementar `sdp_solutions.py` para consultar el módulo de soluciones via API.
- [ ] Definir qué campo en SDP marca una solución como "pública".
- [ ] Conectar la vista `home` con datos reales del API.
- [ ] Configurar variables de entorno (`.env`) para credenciales.
