"""
================================================================================
DOCUMENTACIÓN OFICIAL NICEGUI — SORTABLE CON HANDLE
================================================================================

Use the handle parameter with a CSS selector to restrict dragging to a specific
element. Only the handle element can initiate a drag operation.

    from nicegui import ui

    with ui.card() as card:
        for name in ['Alice', 'Bob', 'Carol']:
            with ui.row().classes('items-center gap-2'):
                ui.icon('drag_indicator') \\
                    .classes('handle cursor-grab active:cursor-grabbing')
                ui.label(name)
    card.make_sortable(handle='.handle')

    ui.run()

================================================================================
CÓMO FUNCIONA EL SORTABLE EN NICEGUI — CONCEPTOS CLAVE
================================================================================

make_sortable() opera sobre los HIJOS DIRECTOS del contenedor al que se llama.
Cuando el usuario arrastra, NiceGUI mueve en el DOM el hijo directo completo.

Estructura mental:

    CONTENEDOR  ← .make_sortable() se llama aquí
    │
    ├── HIJO DIRECTO 1  ← esto es lo que se arrastra (unidad mínima)
    │   ├── icono drag_indicator  ← el handle vive AQUÍ, al mismo nivel
    │   └── ui.expansion(...)     ← el bloque expandible va como hermano
    │
    ├── HIJO DIRECTO 2
    │   ├── icono drag_indicator
    │   └── ui.expansion(...)
    │
    └── HIJO DIRECTO 3
        ├── icono drag_indicator
        └── ui.expansion(...)

POR QUÉ NO FUNCIONA PONER EL HANDLE DENTRO DE LA EXPANSION:
─────────────────────────────────────────────────────────────
Si pones el icono drag_indicator DENTRO del ui.expansion, el handle sí
muestra el cursor de mano (porque la clase CSS funciona), PERO al intentar
arrastrar no pasa nada. El motivo es que el handle necesita ser hermano
del elemento que queremos desplazar — si está anidado dentro de la
expansion, NiceGUI no sabe qué elemento mover (la expansion entera, o solo
lo que hay dentro). La regla: el handle y el contenido arrastrable deben
estar dentro del mismo elemento hijo directo del contenedor sortable.

CORRECTO ✓                              INCORRECTO ✗
──────────────────────────────────────  ────────────────────────────────────
with ui.row():                          with ui.expansion('Título'):
    ui.icon('drag_indicator')               ui.icon('drag_indicator')
        .classes('drag-handle ...')             .classes('drag-handle ...')
    with ui.expansion('Título'):            ui.label('Contenido')
        ui.label('Contenido')

================================================================================
CÓMO INCORPORAR ESTO A TU PÁGINA REAL — GUÍA DE ADAPTACIÓN
================================================================================

ESTRUCTURA EN ESTE EJEMPLO
───────────────────────────
La página está montada así:

    ui.row()                       ← fila principal de dos columnas
    ├── ui.card()                  ← columna izquierda (no relevante)
    └── ui.column() → right_col   ← columna derecha (el contenedor sortable)
        ├── ui.row()               ← HIJO DIRECTO 1 (unidad arrastrable)
        │   ├── ui.icon(...)       ← drag handle
        │   └── ui.expansion(...)  ← bloque expandible
        ├── ui.row()               ← HIJO DIRECTO 2
        └── ui.row()               ← HIJO DIRECTO 3

    right_col.make_sortable(handle='.drag-handle', on_end=...)

AppState en este ejemplo:
    app_state.blocks = [
        {'id': ..., 'title': '...', 'content': '...'},
        ...
    ]
    El índice en la lista == posición visual del bloque.

PASOS PARA ADAPTARLO A TU PÁGINA REAL
──────────────────────────────────────

PASO 1 — Identifica el contenedor de la columna derecha.
    Busca donde defines la columna derecha. Necesitas tener referencia
    a ese elemento. Si hoy tienes algo como:

        with ui.column():          ← sin referencia
            render_blocks(...)

    Cámbialo a:

        with ui.column() as right_col:   ← guarda la referencia
            pass
        render_right_column(right_col, app_state)

PASO 2 — Adapta render_block() para que coincida con tu bloque real.
    En este ejemplo cada bloque tiene 'title' y 'content'. En tu app
    probablemente el bloque tiene más campos. Lo importante es mantener
    la estructura exterior:

        def render_block(block):
            with ui.row().classes('items-center w-full gap-1'):
                #
                # ↓ ESTE ICONO DEBE ESTAR AQUÍ, FUERA DE LA EXPANSION ↓
                #
                ui.icon('drag_indicator').classes(
                    'drag-handle cursor-grab active:cursor-grabbing text-gray-400'
                )
                #
                # ↓ TU BLOQUE EXPANDIBLE REAL VA AQUÍ, COMO HERMANO ↓
                #
                with ui.expansion(block['title']).classes('flex-1'):
                    # ... tu contenido real del bloque ...

    El ui.row() es el envoltorio que hace de "unidad arrastrable".
    Si tus bloques ya usan otro elemento como contenedor (ui.card, etc.),
    ese elemento puede hacer de envoltorio — lo que importa es que el
    handle y la expansion sean hijos del mismo elemento.

PASO 3 — Adapta on_reorder() si tu appstate tiene estructura diferente.
    Si tus bloques no son una lista plana sino un dict, o si necesitas
    hacer una llamada a backend al reordenar, este es el lugar:

        def on_reorder(e, appstate):
            block = appstate.blocks.pop(e.old_index)
            appstate.blocks.insert(e.new_index, block)
            # Agrega aquí lo que necesites: guardar en BD, notificar, etc.

PASO 4 — Llama a make_sortable() DESPUÉS de renderizar todos los bloques.
    No importa si lo haces dentro de render_right_column o directamente
    en la página, pero debe llamarse DESPUÉS de que los bloques ya
    existen en el DOM. En este ejemplo se hace al final de
    render_right_column(), después del loop que crea los bloques.

PASO 5 (si re-renders son necesarios) — Si en tu app se agregan o quitan
    bloques dinámicamente, debes volver a llamar render_right_column()
    completo (hace container.clear() + re-renderiza + vuelve a llamar
    make_sortable). No basta con solo llamar make_sortable de nuevo sobre
    el mismo contenedor porque los nuevos elementos no quedarán registrados.

================================================================================
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any

from nicegui import ui
from nicegui.events import SortableEventArguments


# ---------------------------------------------------------------------------
# Mock AppState
# En el trabajo: reemplazar con el import real, ej:
#   from app.state import app_state
# ---------------------------------------------------------------------------

@dataclass
class AppState:
    blocks: List[Dict[str, Any]] = field(default_factory=list)


app_state = AppState()
app_state.blocks = [
    {'id': 1, 'title': 'Bloque A', 'content': 'Contenido del bloque A. Aquí va información detallada del bloque.'},
    {'id': 2, 'title': 'Bloque B', 'content': 'Contenido del bloque B. Aquí va información detallada del bloque.'},
    {'id': 3, 'title': 'Bloque C', 'content': 'Contenido del bloque C. Aquí va información detallada del bloque.'},
    {'id': 4, 'title': 'Bloque D', 'content': 'Contenido del bloque D. Aquí va información detallada del bloque.'},
]


# ---------------------------------------------------------------------------
# Callback de reordenamiento
# e.old_index → posición original del bloque arrastrado
# e.new_index → posición destino
# NiceGUI ya movió el elemento en el DOM; aquí solo sincronizamos Python.
# ---------------------------------------------------------------------------

def on_reorder(e: SortableEventArguments, appstate: AppState) -> None:
    block = appstate.blocks.pop(e.old_index)
    appstate.blocks.insert(e.new_index, block)
    ui.notify(f'"{block["title"]}" movido a posición {e.new_index + 1}')


# ---------------------------------------------------------------------------
# Render de un bloque individual
#
# ESTRUCTURA CLAVE:
#   ui.row()                ← envoltorio arrastrable (hijo directo del contenedor)
#   ├── ui.icon(drag_...)   ← handle FUERA de la expansion
#   └── ui.expansion(...)   ← bloque expandible como hermano del handle
#
# Adaptar el interior de ui.expansion() para que coincida con el bloque real.
# ---------------------------------------------------------------------------

def render_block(block: Dict[str, Any]) -> None:
    with ui.row().classes('items-center w-full gap-1 py-1'):
        ui.icon('drag_indicator').classes(
            'drag-handle cursor-grab active:cursor-grabbing text-gray-400'
        )
        with ui.expansion(block['title']).classes('flex-1 border rounded'):
            ui.label(block['content']).classes('text-sm text-gray-700')


# ---------------------------------------------------------------------------
# Render de la columna derecha completa
#
# Llama a container.clear() para evitar duplicados si se re-renderiza.
# make_sortable() se llama AL FINAL, después de que todos los bloques existen.
# ---------------------------------------------------------------------------

def render_right_column(container: ui.element, appstate: AppState) -> None:
    container.clear()
    with container:
        for block in appstate.blocks:
            render_block(block)
    container.make_sortable(
        handle='.drag-handle',
        on_end=lambda e: on_reorder(e, appstate),
    )


# ---------------------------------------------------------------------------
# Layout de página
#
# right_col es un ui.column() vacío; render_right_column() lo llena.
# Guarda la referencia (as right_col) para poder pasarla a la función.
# ---------------------------------------------------------------------------

with ui.row().classes('w-full h-screen'):
    with ui.card().classes('w-64 h-full'):
        ui.label('Columna izquierda').classes('text-lg font-bold mb-4')
        ui.label('(No relevante)')

    with ui.column().classes('flex-1 p-4 gap-2') as right_col:
        pass  # se llena en render_right_column()

render_right_column(right_col, app_state)

ui.run(title='NiceGUI Sortable Demo')
