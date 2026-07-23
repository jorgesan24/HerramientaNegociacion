//====================================================
// VARIABLES GLOBALES TABLA
//====================================================

let filas = [];
let filasFiltradas = [];
let paginaActual = 1;

const filasPorPagina = 15;

// ==============================================================
// BLINDAJE DE SEGURIDAD EXCLUSIVO PARA GOOGLE DRIVE EN MÓVILES
// ==============================================================
document.addEventListener("DOMContentLoaded", function() {
    // Buscamos el input file dentro de tu formulario con la clase unificada
    const inputFileNegociacion = document.querySelector(".tarjeta-subida-exclusiva input[type='file']") || document.getElementById("archivoExcelNegociacion");

    if (inputFileNegociacion) {
        inputFileNegociacion.addEventListener("change", function (evento) {
            // 1. Validamos de forma estricta que existan archivos en la cola
            if (!this.files || this.files.length === 0) {
                console.log("SANEM: Cambio detectado en el input pero no se seleccionó ningún archivo.");
                return;
            }

            // CORRECCIÓN CRÍTICA: Extraemos de forma exacta el primer archivo del arreglo
            const archivoSeleccionado = this.files[0];
            
            console.log("SANEM: Evaluando metadatos del elemento cargado:");
            console.log("Nombre real:", archivoSeleccionado.name);
            console.log("Tamaño real:", archivoSeleccionado.size, "bytes");

            // 2. DETECCIÓN CIENTÍFICA DE ENLACES O ARCHIVOS VIRTUALES DE DRIVE EN MÓVILES
            // Rastrea si el nombre contiene extensiones temporales de la nube, prefijos content:// o si reporta 0 bytes en smartphones
            const esEnlaceDriveVirtual = archivoSeleccionado.name.includes(".driveextension") || 
                                         archivoSeleccionado.name.startsWith("content://") || 
                                         (archivoSeleccionado.size === 0 && (navigator.userAgent.includes("Android") || navigator.userAgent.includes("iPhone") || navigator.userAgent.includes("iPad")));

            if (esEnlaceDriveVirtual) {
                // FRENAMOS EN SECO EL SUBMIT ANTES DE QUE VIAJE A FLASK
                evento.preventDefault();
                evento.stopPropagation();
                
                this.value = ""; // Vaciamos el campo por completo para proteger el backend de Flask
                console.warn("SANEM: Intento de subida bloqueado de forma exitosa. Origen: Google Drive Móvil.");

                // Disparamos la alerta de SweetAlert2 estructurada con el formato corporativo
                if (typeof Mensajes !== "undefined" && typeof Mensajes.movil === "function") {
                    Mensajes.movil(
                        "No es posible procesar archivos directamente desde Google Drive en dispositivos móviles. Por favor, descargue el documento Excel a la memoria interna de su teléfono e inténtelo nuevamente.",
                        "Archivo no válido"
                    );
                } else if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "warning",
                        title: "Archivo no válido",
                        text: "No es posible procesar archivos directamente desde Google Drive en dispositivos móviles. Descárguelo a la memoria local de su dispositivo.",
                        confirmButtonText: "Aceptar",
                        confirmButtonColor: "#1565C0",
                        allowOutsideClick: false,
                        heightAuto: false
                    });
                }
            } else {
                // 3. FLUJO EXITOSO: El archivo es un Excel real alojado localmente (en PC o Memoria Interna Móvil)
                console.log("SANEM: Archivo local validado con éxito. Ejecutando envío síncrono...");
                
                // Desplegamos el spinner de carga para dar excelente feedback visual antes de recargar
                if (typeof Swal !== "undefined") {
                    Swal.fire({
                        title: "Procesando Archivo",
                        text: "Analizando la estructura de la negociación, por favor espere...",
                        allowOutsideClick: false,
                        showConfirmButton: false,
                        heightAuto: false,
                        didOpen: () => { 
                            Swal.showLoading(); // Lanza el spinner animado de procesamiento
                        }
                    });
                }
                
                // Forzamos al formulario a despachar los datos limpiamente hacia el servidor
                const formularioPadre = this.closest("form");
                if (formularioPadre) {
                    formularioArchivo.submit();
                }
            }
        });
    }
});

$(function () {

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

cardOtro.classList.add("oculto");

chkOtro.addEventListener("change", function(){

    if(this.checked){

        cardOtro.classList.remove("oculto");

    }else{

        cardOtro.classList.add("oculto");

        document.getElementById("plan_otro").value="";

    }

});

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

            const validacion = celdas[8]?.innerText.trim().toUpperCase() || "";

            const estado = celdas[9]?.innerText.trim().toUpperCase() || "";

            const duplicado = celdas[10]?.innerText.trim().toUpperCase() || "";

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

    buscador.addEventListener("keyup", filtrarTabla);

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

            combo.value = mapaTarjetas[filtro] || "todos";

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