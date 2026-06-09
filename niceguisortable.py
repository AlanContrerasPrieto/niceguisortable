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




# //SEC Tab_bloques
def _build_bloques_tab(state: AppState, image_broker: ImageBroker):
    """Punto de entrada del tab de bloques. Firma idéntica al original."""
    ui.add_head_html('''
        <style>
        .no-preview .q-uploader__list {
        display: none;
        }
        </style>
        ''')
    ui.add_head_html(
        '<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js"></script>'
    )
    refs = {"block_list": None}

    with ui.row().classes("w-full gap-4").style("align-items: flex-start;"):

        # PIN Columna izquierda: agregar bloques
        with ui.card().style("flex: 60; min-width: 0;"):
            ui.label("Agregar bloque").classes("section-header")
            ui.separator()

            tipo_toggle = ui.toggle(TIPO_OPTIONS, value="templates") \
                .classes("w-full justify-center")

            ui.separator().style("margin: 12px 0;")

            adder_slot = ui.column().classes("w-full")

        # PIN Columna derecha: lista de bloques
        with ui.card().style("flex: 40; min-width: 0;"):
            ui.label("Bloques actuales").classes("section-header")
            ui.separator()

            @ui.refreshable
            def block_list():
                if not state.bloques:
                    ui.label("Aún no hay bloques.").style("color: #888; font-style: italic;")
                    return

                def make_move(idx: int, direction: str):
                    def move():
                        bloques = state.bloques
                        n = len(bloques)
                        if direction == "top" and idx > 0: b = bloques.pop(idx); bloques.insert(0, b)
                        elif direction == "up" and idx > 0: b = bloques.pop(idx); bloques.insert(idx-1, b)
                        elif direction == "down" and idx < n-1: b = bloques.pop(idx); bloques.insert(idx+1, b)
                        elif direction == "bottom" and idx < n-1: b = bloques.pop(idx); bloques.append(b)
                        block_list.refresh()
                    return move

                def make_delete(idx):
                    def dlt():
                        state.bloques.pop(idx)
                        block_list.refresh()
                        ui.notify("🗑️ Bloque eliminado", type="warning")
                    return dlt

                def make_edit(blk_id):
                    def edit():
                        _open_edit_dialog(state, blk_id, block_list, image_broker)
                    return edit

                with ui.column().classes('w-full gap-1') as sortable_col:
                    for i, bloque in enumerate(state.bloques):
                        tipo = bloque["tipo"]
                        handler = HANDLERS.get(tipo)

                        if handler is None:
                            with ui.row().classes('items-center w-full gap-1'):
                                ui.icon('drag_indicator').classes(
                                    'drag-handle cursor-grab active:cursor-grabbing text-gray-400'
                                )
                                ui.label(f"⚠️ Bloque #{i+1} con tipo desconocido: {tipo}") \
                                    .style("color:#cc0000;")
                            continue

                        # Tools → render compacto inline
                        if handler.is_tool:
                            with ui.row().classes('items-center w-full gap-1'):
                                ui.icon('drag_indicator').classes(
                                    'drag-handle cursor-grab active:cursor-grabbing text-gray-400'
                                )
                                with ui.element():
                                    handler.render_tool_row(bloque, i, make_move, make_delete, make_edit)
                            continue

                        # Bloques normales → expansion
                        etiqueta_tipo = handler.get_label(bloque)
                        resumen = handler.get_summary(bloque)
                        caption = etiqueta_tipo
                        if resumen:
                            caption += f" | {resumen}"

                        with ui.row().classes('items-center w-full gap-1'):
                            ui.icon('drag_indicator').classes(
                                'drag-handle cursor-grab active:cursor-grabbing text-gray-400'
                            )
                            with ui.expansion().classes("flex-1 block-card") \
                                    .style("margin-bottom: 4px;") as exp:
                                with exp.add_slot("header"):
                                    with ui.row().classes("w-full items-center gap-2") \
                                            .style("flex-wrap: nowrap;"):
                                        ui.label(f"{i+1}").classes("text-xs text-gray-500") \
                                            .style("min-width: 22px;")
                                        ui.label(caption).classes("flex-1") \
                                            .style("font-weight: 600; overflow: hidden; "
                                                   "text-overflow: ellipsis; white-space: nowrap;")
                                        ui.button("✏️ Editar",
                                                  on_click=make_edit(bloque["id"])) \
                                            .props("flat dense").style("color: #0063A6;") \
                                            .on("click.stop")

                                # Fila inferior de botones: mover (izq) + eliminar (der)
                                with ui.row().classes("w-full gap-2 items-center"):
                                    ui.button(icon="keyboard_double_arrow_up", on_click=make_move(i, "top"))
                                    ui.button(icon="keyboard_arrow_up", on_click=make_move(i, "up"))
                                    ui.button(icon="keyboard_arrow_down", on_click=make_move(i, "down"))
                                    ui.button(icon="keyboard_double_arrow_down", on_click=make_move(i, "bottom"))
                                    ui.space()
                                    ui.button("🗑️ Eliminar",
                                              on_click=make_delete(i)) \
                                        .props("flat").style("color: #cc0000;")

                                ui.separator().style("margin: 8px 0;")
                                handler.render_preview(bloque)

                ui.run_javascript(f'''
                    setTimeout(function() {{
                        var el = getElement("{sortable_col.id}");
                        if (!el || el._sortable_init) return;
                        el._sortable_init = true;
                        new Sortable(el, {{
                            handle: ".drag-handle",
                            animation: 150,
                            onEnd: function(evt) {{
                                emitEvent("bloques-reorder",
                                    {{old_index: evt.oldIndex, new_index: evt.newIndex}});
                            }}
                        }});
                    }}, 100);
                ''')

            block_list()

    def on_reorder_js(args: dict):
        bloque = state.bloques.pop(args['old_index'])
        state.bloques.insert(args['new_index'], bloque)
        block_list.refresh()

    ui.on('bloques-reorder', lambda e: on_reorder_js(e.args))

    # Ahora que block_list ya existe, definimos el block_adder dentro del
    # contenedor reservado en la columna izquierda (adder_slot) y lo
    # cableamos al toggle.
    refs["block_list"] = block_list

    @ui.refreshable
    def block_adder():
        handler = FORM_HANDLERS.get(tipo_toggle.value)
        if handler is None:
            ui.label(f"⚠️ Tipo no soportado: {tipo_toggle.value}") \
                .style("color: #cc0000;")
            return
        handler.render_form(state, refs["block_list"], image_broker)

    def _refresh_adder():
        adder_slot.clear()
        with adder_slot:
            block_adder()

    tipo_toggle.on("update:model-value", lambda _: _refresh_adder())

    with adder_slot:
        block_adder()
# endregion //!SEC