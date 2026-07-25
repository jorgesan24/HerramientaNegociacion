//====================================================
// VARIABLES GLOBALES TABLA
//====================================================

let filas = [];
let filasFiltradas = [];
let paginaActual = 1;

const filasPorPagina = 15;

// ==============================================================
// VALIDACIÓN FILTRADA CON TRY-CATCH PARA DRIVE EN MÓVILES (FIJADO)
// ==============================================================
document.addEventListener("DOMContentLoaded", function() {
    const inputArchivoNeg = document.getElementById("archivoExcelNegociacion");

    if (inputArchivoNeg) {
        inputArchivoNeg.addEventListener("change", function (evento) {
            // 1. Validación básica preventiva de selección
            if (!this.files || this.files.length === 0) return;

            try {
                // Capturamos el archivo de forma directa
                const archivo = this.files[0];
                console.log("SANEM: Evaluando metadatos en try...catch ->", archivo.name);

                // 2. DETECCIÓN ESTÁNDAR DE ARCHIVOS PROBLEMÁTICOS DE DRIVE
                const esDesdeDrive = archivo.name.includes(".driveextension") ||
                                     archivo.name.startsWith("content://") ||
                                     (archivo.size === 0 && (navigator.userAgent.includes("Android") || navigator.userAgent.includes("iPhone")));

                if (esDesdeDrive) {
                    // Forzamos el error de forma manual para saltar de inmediato al bloque catch
                    throw new Error("GoogleDriveMobileDetected");
                }

                // ==========================================================
                // FLUJO VÁLIDO: El archivo es un Excel local real (PC o Móvil)
                // ==========================================================
                console.log("SANEM: Archivo local aprobado por el try. Desplegando indicador...");
                
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
                // El HTML con su delay en el onchange procesará el submit() nativo automáticamente

            } catch (error) {
                // ==========================================================
                // INTERCEPCIÓN CONTROLADA: Captura fallas y bloquea Drive móvil
                // ==========================================================
                console.error("SANEM Catch: Se interceptó un archivo inválido o error de metadatos.", error);
                
                // Bloqueamos en seco el submit del formulario para que no se salga de la página
                evento.preventDefault();
                evento.stopPropagation();
                
                // Vaciamos el input para proteger el backend de Flask
                inputArchivoNeg.value = ""; 

                // Disparamos tu alerta corporativa controlada sin tumbar la sesión
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