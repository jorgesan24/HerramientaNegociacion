//====================================================
// VARIABLES GLOBALES TABLA
//====================================================

let filas = [];
let filasFiltradas = [];
let paginaActual = 1;

const filasPorPagina = 15;

// ==============================================================
// VALIDACIÓN FILTRADA DE GOOGLE DRIVE EN MÓVILES (CORREGIDO)
// ==============================================================
document.addEventListener("DOMContentLoaded", function() {
    const inputArchivoNeg = document.getElementById("archivoExcelNegociacion");

    if (inputArchivoNeg) {
        inputArchivoNeg.addEventListener("change", function (evento) {
            // 1. Validamos que el usuario realmente haya seleccionado un archivo
            if (!this.files || this.files.length === 0) return;

            // PASO MAESTRO: Extraemos el primer archivo individual para leer el nombre real
            const archivo = this.files[0];
            console.log("SANEM Movil: Validando cambio de archivo:", archivo.name, "| Tamaño:", archivo.size);

            // 2. DETECCIÓN ESTÁNDAR: Solo si cumple estas condiciones estrictas de Drive en celular
            const esDesdeDrive = archivo.name.includes(".driveextension") ||
                                 archivo.name.startsWith("content://") ||
                                 (archivo.size === 0 && (navigator.userAgent.includes("Android") || navigator.userAgent.includes("iPhone")));

            if (esDesdeDrive) {
                // Bloqueamos por completo el envío automático para que no se salga de la página
                evento.preventDefault();
                evento.stopPropagation();
                
                this.value = ""; // Limpiamos el input por protección
                console.warn("SANEM Movil: Bloqueado archivo virtual de Google Drive.");

                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "warning",
                        title: "Archivo no válido",
                        text: "No es posible procesar archivos directamente desde Google Drive en dispositivos móviles. Por favor, descargue el documento Excel a la memoria interna de su teléfono e inténtelo nuevamente.",
                        confirmButtonText: "Aceptar",
                        confirmButtonColor: "#1565C0",
                        allowOutsideClick: false,
                        heightAuto: false
                    });
                }
            } else {
                // 3. ARCHIVO LOCAL VÁLIDO (PC o Memoria Interna Celular):
                // Dejamos que el delay en el 'onchange' del HTML haga el submit de forma nativa
                console.log("SANEM: Archivo local aprobado. Desplegando indicador de carga.");
                
                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        title: "Procesando Archivo",
                        text: "Analizando la estructura de la negociación, por favor espere...",
                        allowOutsideClick: false,
                        showConfirmButton: false,
                        heightAuto: false,
                        didOpen: () => { Swal.showLoading(); }
                    });
                }
            }
        });
    }
});

$(function () {

    // ==============================================================
    // SELECCIÓN VISUAL FIJA PARA LAS HOJAS DE EXCEL (RESUELTO CON LABELS)
    // ==============================================================
    // Intercepta el click sobre las etiquetas label de las hojas cargadas
    $(document).on("click", ".lista-hojas .item-hoja", function (e) {
        console.log("SANEM: Capturando selección de hoja física ->", $(this).find(".nombre-hoja").text().trim());

        // 1. Removemos la clase de selección previa de todas las demás tarjetas de la lista
        $(".lista-hojas .item-hoja").css({
            "background-color": "transparent",
            "color": "#4A6585",
            "border": "1px solid #D6E2F1"
        }).removeClass("seleccionada");

        // 2. Aplicamos el sombreado azul pastel corporativo de forma fija a la hoja clickeada
        $(this).css({
            "background-color": "#EAF3FF",
            "color": "#0D47A1",
            "border": "1px solid #B3D7FF"
        }).addClass("seleccionada");
        
        // Forzamos al radio button interno a marcarse por si el click dio en el texto o la imagen
        $(this).find("input[type='radio']").prop("checked", true);
    });

    //==========================
    // Abrir modal
    //==========================

    $("#btnExportar").on("click", function () {
        $("#modalExportar").addClass("activo");
        $("body").css("overflow", "hidden");
    });

    //==========================
    // Cerrar modal (X)
    //==========================

    $("#cerrarModal").on("click", cerrarModal);

    //==========================
    // Cerrar modal (Cancelar)
    //==========================

    $("#cancelarModal").on("click", cerrarModal);

    //==========================
    // Cerrar al hacer click fuera
    //==========================

    $("#modalExportar").on("click", function (e) {
        if (e.target === this) {
            cerrarModal();
        }
    });

    //==========================
    // Cerrar con ESC
    //==========================

    $(document).on("keydown", function (e) {
        if (e.key === "Escape") {
            cerrarModal();
        }
    });

    //==========================
    // Función común
    //==========================

    function cerrarModal() {
        $("#modalExportar").removeClass("activo");
        $("body").css("overflow", "auto");
    }

});

//====================================
// Selección visual de tarjetas
//====================================

$(".opcion-card input").on("change", function(){

    const grupo = $(this).attr("name");

    $("input[name='"+grupo+"']")
        .closest(".opcion-card")
        .removeClass("seleccionada");

    $(this)
        .closest(".opcion-card")
        .addClass("seleccionada");

});

//====================================
// Mostrar campo "Otro Plan"
//====================================

const chkOtro = document.getElementById("planOtro");
const cardOtro = document.getElementById("planOtroCard");

if (cardOtro) {
    cardOtro.classList.add("oculto");
}

if (chkOtro && cardOtro) {
    chkOtro.addEventListener("change", function(){
        if(this.checked){
            cardOtro.classList.remove("oculto");
        }else{
            cardOtro.classList.add("oculto");
            document.getElementById("plan_otro").value="";
        }
    });
}

$(document).ready(function () {

    $("#toggleValidacion").off("click").on("click", function () {
        $("#contenidoValidacion").slideToggle(250);
        const icono = $("#iconoToggleValidacion");
        icono.text(
            icono.text() === "▲"
            ? "▼"
            : "▲"
        );
    });

    $("#toggleHojas").off("click").on("click", function () {
        $("#contenidoHojas").slideToggle(250);
        const icono = $("#iconoToggleHojas");
        icono.text(
            icono.text() === "▲"
            ? "▼"
            : "▲"
        );
        $("#panelTabla").toggleClass("expandida");
    });

});

//====================================================
// FILTROS DE LA TABLA
//====================================================
const mapaTarjetas = {
    registros: "todos",
    aceptables: "ACEPTAR",
    renegociar: "RENEGOCIAR",
    duplicados: "DUPLICADO",
    activos: "ACTIVO",
    no_activos: "NO ACTIVO"
};

function renderizarPagina() {

    const totalPaginas = Math.max(
        1,
        Math.ceil(filasFiltradas.length / filasPorPagina)
    );

    if (paginaActual > totalPaginas)
        paginaActual = totalPaginas;

    const inicio = (paginaActual - 1) * filasPorPagina;
    const fin = inicio + filasPorPagina;

    filas.forEach(f => f.style.display = "none");

    filasFiltradas
        .slice(inicio, fin)
        .forEach(f => f.style.display = "");

    const contador = document.getElementById("contadorResultadosBuscador");

    if (contador) {
        contador.innerHTML = `
        Resultados encontrados:
        <strong>${filasFiltradas.length}</strong>
        |
        Página
        <strong>${paginaActual}</strong>
        de
        <strong>${totalPaginas}</strong>
        `;
    }
    construirPaginador(totalPaginas);
}

document.addEventListener("DOMContentLoaded", () => {

    const tabla = document.getElementById("tablaNegociacion");

    if (!tabla) return;

    filas = [...tabla.querySelectorAll("tbody tr")];

    const buscador = document.getElementById("buscarTabla");
    const combo = document.getElementById("filtroTabla");
    const contador = document.getElementById("contadorResultadosBuscador");

    function filtrarTabla() {

        filasFiltradas = [];

        const texto = buscador.value.toLowerCase().trim();
        const filtro = combo.value;

        filas.forEach(fila => {

            const celdas = fila.querySelectorAll("td");
            const contenido = fila.innerText.toLowerCase();

            // Respaldo de seguridad indexado por celdas reales para evitar congelamientos
            const validacion = celdas[8] ? celdas[8].innerText.trim().toUpperCase() : "";
            const estado = celdas[9] ? celdas[9].innerText.trim().toUpperCase() : "";
            const duplicado = celdas[10] ? celdas[10].innerText.trim().toUpperCase() : "";


            let mostrar = contenido.includes(texto);

            if (mostrar) {
                switch (filtro) {
                    case "ACEPTAR":
                        mostrar = validacion === "ACEPTAR";
                        break;
                    case "RENEGOCIAR":
                        mostrar = validacion === "RENEGOCIAR";
                        break;
                    case "DUPLICADO":
                        mostrar = duplicado === "DUPLICADO";
                        break;
                    case "ACTIVO":
                        mostrar = [
                            "VIGENTE",
                            "EN TRAMITE RENOV",
                            "DROGA BLANCA",
                            "PAÑALES",
                            "APME",
                            "MVND"
                        ].includes(estado);
                        break;
                    case "NO ACTIVO":
                        mostrar = [
                            "VENCIDO",
                            "NEGADO",
                            "TEMP. NO COMERC - VIGENTE",
                            "ABANDONO",
                            "TEMP. NO COMERCIALIZADO - EN TRÁMITE RENOV",
                            "NO EXISTE",
                            "REVOCADO",
                            "COMERCIALIZADO SOLO POR EXPORTACION",
                            "SUSPENDIDO",
                            "NO APLICA REGISTRO",
                            "INACTIVO",
                            "MUESTRA MEDICA",
                            "DESISTIDO",
                            "CANCELADO",
                            "PERDIDA FUERZA EJEC"
                        ].includes(estado);
                        break;
                }
            }

            if (mostrar) {
                filasFiltradas.push(fila);
            }

        });

        if (contador) {
            paginaActual = 1;
            renderizarPagina();
        }
    }

    if (buscador) buscador.addEventListener("keyup", filtrarTabla);

    if (combo) {
        combo.addEventListener("change", () => {
            document
                .querySelectorAll(".indicador-card")
                .forEach(c => c.classList.remove("activo"));

            const tarjeta = Object.keys(mapaTarjetas)
                .find(k => mapaTarjetas[k] === combo.value);

            if (tarjeta) {
                document
                    .querySelector(`.indicador-card[data-filtro="${tarjeta}"]`)
                    ?.classList.add("activo");
            }
            filtrarTabla();
        });
    }

    document
        .querySelectorAll(".indicador-card[data-filtro]")
        .forEach(card => {
            card.addEventListener("click", function () {
                // Quitar selección anterior
                document
                    .querySelectorAll(".indicador-card")
                    .forEach(c => c.classList.remove("activo"));

                // Activar tarjeta
                this.classList.add("activo");

                // Cambiar el combo
                const filtro = this.dataset.filtro;
                if (combo) combo.value = mapaTarjetas[filtro] || "todos";

                // Aplicar filtro
                filtrarTabla();
            });
        });

    filtrarTabla();

});

function construirPaginador(totalPaginas) {

    const paginador = document.getElementById("paginadorTabla");

    if (!paginador) return;

    paginador.innerHTML = "";

    // Botón anterior
    const anterior = document.createElement("button");
    anterior.className = "btn-pagina";
    anterior.textContent = "◀ Anterior";
    anterior.disabled = paginaActual === 1;

    anterior.onclick = () => {
        paginaActual--;
        renderizarPagina();
    };

    // Texto central
    const info = document.createElement("span");
    info.className = "texto-pagina";
    info.textContent = `Página ${paginaActual} de ${totalPaginas}`;

    // Botón siguiente
    const siguiente = document.createElement("button");
    siguiente.className = "btn-pagina";
    siguiente.textContent = "Siguiente ▶";
    siguiente.disabled = paginaActual === totalPaginas;

    siguiente.onclick = () => {
        paginaActual++;
        renderizarPagina();
    };

    paginador.appendChild(anterior);
    paginador.appendChild(info);
    paginador.appendChild(siguiente);
}