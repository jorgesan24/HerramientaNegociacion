document.addEventListener("DOMContentLoaded", function () {
    const radios = document.querySelectorAll('input[name="tipo_filtro"]');
    const busquedaTexto = document.getElementById("busquedaTexto");
    const busquedaRegional = document.getElementById("busquedaRegional");
    const lblCriterio = document.getElementById("lblCriterio");

    // Validamos la existencia para evitar que el script falle y congele el formulario
    const inputTexto = busquedaTexto ? busquedaTexto.querySelector('input[type="text"]') : null;
    const selectRegional = busquedaRegional ? busquedaRegional.querySelector('select') : null;

    // ======================================================
    // LIMPIAR PANEL AL INICIAR UNA NUEVA BÚSQUEDA
    // ======================================================
    if (inputTexto) {
        inputTexto.addEventListener("focus", limpiarPanelReferencia);
    }

    if (selectRegional) {
        selectRegional.addEventListener("focus", limpiarPanelReferencia);
    }

    // ======================================================
    // VALIDACIÓN INTERNA Y SPINNER DE CARGA AL BUSCAR
    // ======================================================
    const frmReferencia = document.getElementById("frmReferencia");

    if (frmReferencia) {
        frmReferencia.addEventListener("submit", function (e) {
            const tipoSeleccionado = document.querySelector('input[name="tipo_filtro"]:checked').value;

            // 1. Validaciones preventivas de campos obligatorios
            if (tipoSeleccionado === "REGIONAL") {
                if (!selectRegional || selectRegional.value.trim() === "") {
                    e.preventDefault();
                    if (typeof Mensajes !== "undefined" && typeof Mensajes.warning === "function") {
                        Mensajes.warning("Seleccione una regional.");
                    }
                    return;
                }
            } else {
                if (!inputTexto || inputTexto.value.trim() === "") {
                    e.preventDefault();
                    if (typeof Mensajes !== "undefined" && typeof Mensajes.warning === "function") {
                        Mensajes.warning("Ingrese un criterio de búsqueda.");
                    }
                    return;
                }
            }

            // 2. PASO CLAVE: Si los campos son válidos, activamos el Spinner de procesamiento
            if (typeof Swal !== "undefined") {
                Swal.fire({
                    title: "Buscando Medicamento",
                    text: "Consultando la base de datos de referencia, por favor espere...",
                    allowOutsideClick: false,
                    allowEscapeKey: false,
                    showConfirmButton: false, // Oculta el botón de aceptación
                    heightAuto: false,
                    didOpen: () => {
                        Swal.showLoading(); // Lanza la animación nativa del spinner
                    }
                });
            }
            
            // El formulario continúa su viaje normal (POST/GET) hacia Flask con la pantalla bloqueada
        });
    }

    const nombresEtiquetas = {
        "CUM": "Código CUM",
        "P. ACTIVO": "Principio Activo",
        "GRUPO TERAPEUTICO": "Grupo Terapéutico",
        "NIT": "NIT Proveedor",
        "REGIONAL": "Regional"
    };

    function alternarBuscadores(evento) {
        const seleccionado = document.querySelector('input[name="tipo_filtro"]:checked');
        
        if (evento && evento.type === "change") {
            if (inputTexto) inputTexto.value = ""; 
            if (selectRegional) selectRegional.value = ""; 
        }

        if (seleccionado && nombresEtiquetas[seleccionado.value]) {
            if (lblCriterio) lblCriterio.textContent = nombresEtiquetas[seleccionado.value];
        }

        if (busquedaTexto && busquedaRegional) {
            if (seleccionado && seleccionado.value === "REGIONAL") {
                busquedaTexto.classList.add("oculto");
                busquedaRegional.classList.remove("oculto");
            } else {
                busquedaTexto.classList.remove("oculto");
                busquedaRegional.classList.add("oculto");
            }
        }
    }

    // Vinculamos los eventos de manera segura a los radio buttons de filtrado
    if (radios.length > 0) {
        radios.forEach(radio => {
            radio.addEventListener("change", function (e) {
                // Primero llamamos a la limpieza absoluta (URL, Botón y Paneles)
                limpiarPanelReferencia();
                // Luego alternamos la visualización de los cuadros de búsqueda correspondientes
                alternarBuscadores(e);
            });
        });
        alternarBuscadores();
    }

    // ==============================================================
    // LÓGICA DEL TEXTBOX "OTRO" (Insertada de forma segura)
    // ==============================================================
    const inputPlanOtro = document.getElementById("planOtro");
    const contenedorPlanOtro = document.getElementById("planOtroCard");

    if (inputPlanOtro && contenedorPlanOtro) {
        document.querySelectorAll('input[name="plan"]').forEach(radio => {
            radio.addEventListener("change", function () {
                if (inputPlanOtro.checked) {
                    contenedorPlanOtro.classList.remove("card-texto-oculto");
                } else {
                    contenedorPlanOtro.classList.add("card-texto-oculto");
                }
            });
        });
    }
});

// ==============================================================
// CONTROL GLOBAL DEL MODAL (CIERRE Y CONTROL DE CLICS)
// ==============================================================

// Función global para controlar el cierre del modal
function cerrarElModalNativo() {
    const modal = document.getElementById('modalDetalleFacturacion');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restaura el scroll del fondo
    }
}

// Variable global para almacenar el código activo en memoria
let codigoSeleccionado = "";

// Lógica para interceptar el clic sobre las filas de la tabla principal
document.querySelectorAll(".fila-medicamento").forEach(fila => {
    fila.addEventListener("click", function () {
        // 1. Limpiamos la clase visual de todas las demás filas
        document.querySelectorAll(".fila-medicamento")
            .forEach(f => f.classList.remove("fila-seleccionada"));

        // 2. Marcamos con fondo azul la fila a la que se le hizo clic
        this.classList.add("fila-seleccionada");

        // 3. CORRECCIÓN ROBUSTA: Intentamos leer data-codigo, data-cum o directamente la primera celda TD (CUM)
        let celdaCUM = this.querySelector("td") ? this.querySelector("td").innerText.trim() : "";
        codigoSeleccionado = this.dataset.codigo || this.dataset.cum || celdaCUM || "";
        
        console.log("Fila seleccionada de forma física. Código extraído:", codigoSeleccionado);

        // 4. PASO CLAVE: Transferimos el código al atributo 'data-cum' del botón Detalle
        const botonDetalle = document.getElementById("btnDetalle");
        if (botonDetalle && codigoSeleccionado) {
            botonDetalle.setAttribute("data-cum", codigoSeleccionado);
            console.log("Atributo 'data-cum' actualizado con éxito en el botón Detalle.");
        }
    });
});

// Función maestra de apertura de la ventana emergente por AJAX (Corregida con Spinner)
function abrirDetalleFacturacionModal(boton, evento) {
    evento.preventDefault();
    evento.stopPropagation();

    // 1. Intentamos leer el CUM desde el atributo del botón que inyectó Flask
    let codigo = boton.getAttribute('data-cum');

    // 2. RESPALDO 1: Si está vacío, buscamos en los parámetros reales de la URL actual de la barra de direcciones
    if (!codigo || codigo.trim() === "") {
        const urlParams = new URLSearchParams(window.location.search);
        codigo = urlParams.get('codigo') || urlParams.get('filtro') || "";
    }

    // 3. RESPALDO 2: Si sigue vacío, leemos la primera celda TD de la fila que esté sombreada
    const tieneFilaActiva = document.querySelector(".fila-medicamento.fila-seleccionada");
    if ((!codigo || codigo.trim() === "") && tieneFilaActiva) {
        const primeraCelda = tieneFilaActiva.querySelector("td");
        if (primeraCelda) {
            codigo = primeraCelda.innerText.trim();
        }
    }

    console.log("-> Procesando apertura con Spinner. CUM resuelto:", codigo);

    // 4. VALIDACIÓN CRÍTICA CORRECTA: Solo se detiene si el código está totalmente vacío por todos los medios
    if (!codigo || codigo.trim() === "") {
        if (typeof Mensajes !== "undefined" && typeof Mensajes.warning === "function") {
            Mensajes.warning(
                "Por favor, seleccione un medicamento de la lista haciendo clic sobre la fila antes de consultar el detalle.",
                "Selección Requerida"
            );
        } else if (typeof Swal !== "undefined") {
            Swal.fire({
                icon: "warning",
                title: "Selección Requerida",
                text: "Por favor, seleccione un medicamento de la lista haciendo clic sobre la fila antes de consultar el detalle.",
                confirmButtonText: "Aceptar",
                confirmButtonColor: "#D97706",
                allowOutsideClick: false,
                heightAuto: false
            });
        }
        return; // Frena la operación si no hay datos
    }

    // ==============================================================
    // ACTIVA EL SPINNER DE CARGA (SWEETALERT2)
    // ==============================================================
    if (typeof Swal !== "undefined") {
        Swal.fire({
            title: "Procesando Consulta",
            text: "Cargando detalle de facturación, por favor espere...",
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false, 
            heightAuto: false,
            didOpen: () => {
                Swal.showLoading(); 
            }
        });
    }

    // 5. Flujo normal de carga por AJAX hacia el modal
    const modal = document.getElementById('modalDetalleFacturacion');
    const modalContent = document.getElementById('modalBodyContent');

    if (!modal || !modalContent) {
        if (typeof Swal !== "undefined") Swal.close(); 
        console.error("ERROR: No se encontraron los contenedores del modal.");
        return;
    }

    const urlDestino = "/detalle/" + encodeURIComponent(codigo.trim());

    fetch(urlDestino, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => {
        if (!response.ok) throw new Error("El servidor Flask devolvió un error " + response.status);
        return response.text();
    })
    .then(html => {
        // CERRAMOS EL SPINNER JUSTO ANTES DE INYECTAR EL MODAL
        if (typeof Swal !== "undefined") {
            Swal.close();
        }

        modalContent.innerHTML = html;
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden'; 

        const btnCerrar = document.getElementById('btnCerrarModal');
        if (btnCerrar) {
            btnCerrar.addEventListener('click', cerrarElModalNativo);
        }
        
        // Ejecución de la paginación interna de la tabla del modal
        setTimeout(() => {
            const filasModal = modalContent.querySelectorAll(".tabla-detalle tbody tr");
            const registrosPorPagina = 20;
            let paginaActual = 1;
            const totalRegistros = filasModal.length;
            const totalPaginas = Math.ceil(totalRegistros / registrosPorPagina);

            if (totalRegistros > registrosPorPagina) {
                const bloquePag = document.getElementById("paginacionModalBloque");
                if (bloquePag) bloquePag.style.display = "flex";

                function actualizarTablaModal() {
                    const inicio = (paginaActual - 1) * registrosPorPagina;
                    const fin = inicio + registrosPorPagina;
                    filasModal.forEach((fila, indice) => {
                        fila.style.display = (indice >= inicio && indice < fin) ? "" : "none";
                    });
                    const txtInfo = document.getElementById("infoPaginacionModal");
                    if (txtInfo) txtInfo.textContent = `Mostrando registros del ${inicio + 1} al ${Math.min(fin, totalRegistros)} de ${totalRegistros}`;
                    document.getElementById("btnPrevModal").disabled = (paginaActual === 1);
                    document.getElementById("btnNextModal").disabled = (paginaActual === totalPaginas);
                }

                const btnPrev = document.getElementById("btnPrevModal");
                const btnNext = document.getElementById("btnNextModal");
                if (btnPrev && btnNext) {
                    btnPrev.replaceWith(btnPrev.cloneNode(true));
                    btnNext.replaceWith(btnNext.cloneNode(true));
                    document.getElementById("btnPrevModal").addEventListener("click", () => {
                        if (paginaActual > 1) { paginaActual--; actualizarTablaModal(); document.querySelector(".detalle-tabla").scrollTop = 0; }
                    });
                    document.getElementById("btnNextModal").addEventListener("click", () => {
                        if (paginaActual < totalPaginas) { paginaActual++; actualizarTablaModal(); document.querySelector(".detalle-tabla").scrollTop = 0; }
                    });
                }
                actualizarTablaModal();
            }
        }, 50);
    })
    .catch(error => {
        console.error("Error detectado en el proceso:", error);
        if (typeof Swal !== "undefined") Swal.close();
        
        if (typeof Mensajes !== "undefined" && typeof Mensajes.error === "function") {
            Mensajes.error(
                "No se pudo cargar el detalle de facturación para el medicamento seleccionado.",
                "Error de Carga"
            );
        }
    });
}

// Cierra el modal si se hace clic fuera de la tarjeta (en la capa oscura)
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('modalDetalleFacturacion');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                cerrarElModalNativo();
            }
        });
    }
});

// ======================================================
// LIMPIAR PANEL DERECHO, TABLA INTERNA, BOTÓN Y URL
// ======================================================
function limpiarPanelReferencia() {
    console.log("-> Ejecutando limpieza absoluta y bloqueo controlado de la interfaz.");

    // 1. Limpiamos los textos dentro de las tarjetas del panel derecho
    document.querySelectorAll(".panel-derecho .tarjeta-ref p").forEach(p => {
        p.textContent = "-";
    });

    // Restablecemos el título principal por defecto
    const titulo = document.querySelector(".tarjeta-segun .Titulo");
    if (titulo) {
        titulo.textContent = "Valor Referencia";
    }

    // 2. Limpieza instantánea de la barra de direcciones (URL)
    const rutaLimpia = window.location.protocol + "//" + window.location.host + window.location.pathname;
    window.history.replaceState({ path: rutaLimpia }, '', rutaLimpia);

    // 3. Vaciamos el CUM asignado al botón Detalle
    const botonDetalle = document.getElementById("btnDetalle");
    if (botonDetalle) {
        botonDetalle.setAttribute("data-cum", "");
    }

    // 4. RESTAURAR CONTADORES SUPERIORES DE LA TABLA A CERO
    const contador = document.getElementById("contadorResultadosBuscador");
    if (contador) {
        contador.innerHTML = `
            Resultados encontrados: <strong>0</strong> | 
            Página: <strong>1</strong> de <strong>1</strong>
        `;
    }

    // 5. INHABILITAR EL BOTÓN EXPORTAR DEL PANEL SUPERIOR
    // Buscamos el botón de exportar de la barra de acciones
    const btnExportarPrincipal = document.querySelector(".link-exportar button") || document.getElementById("btnExportar");
    if (btnExportarPrincipal) {
        btnExportarPrincipal.disabled = true;
        btnExportarPrincipal.style.opacity = "0.5";
        btnExportarPrincipal.style.cursor = "not-allowed";
        
        // Desvinculamos temporalmente el enlace superior de redirección para que no haga nada
        const enlacePadre = btnExportarPrincipal.closest("a");
        if (enlacePadre) {
            enlacePadre.removeAttribute("href");
        }
    }

    // 6. INYECTAR FILA VACÍA EN LA TABLA CON EL MENSAJE ORIGINAL
    const tbody = document.getElementById("tbodyResultadosBuscador");
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align:center;padding:40px;color:#777;font-weight: 500;">
                    No hay información para mostrar
                </td>
            </tr>
        `;
    }

    // 7. OCULTAR O RECOMPACTAR LOS BOTONES DE PAGINACIÓN INFERIORES
    const paginacionBloque = document.getElementById("bloquePaginacionBuscador");
    if (paginacionBloque) {
        // Removemos los botones 'Anterior' y 'Siguiente' para que solo quede el indicador central
        paginacionBloque.querySelectorAll("a").forEach(a => a.remove());
        const spanTxt = document.getElementById("txtPaginaActualBuscador");
        if (spanTxt) {
            spanTxt.textContent = "Página 1 de 1";
        }
    }
}

// ==============================================================
// DELEGACIÓN GLOBAL PARA EL BOTÓN EXPORTAR DEL MODAL (RESOLUCIÓN)
// ==============================================================
document.addEventListener("click", function (evento) {
    // Verificamos si el elemento clickeado es el botón de exportar o la imagen dentro de él
    const botonExportar = evento.target.closest("#btnExportarExcelModal");
    
    if (botonExportar) {
        evento.preventDefault();
        evento.stopPropagation();
        
        console.log("-> Capturando click dinámico en el exportador del modal.");

        const contenedorModal = document.getElementById("modalBodyContent");
        if (!contenedorModal) {
            console.error("No se encontró el contenedor del modal.");
            return;
        }

        // 1. Inicializamos la plantilla XML estructurada para Excel
        let excelTemplate = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://w3.org">`;
        excelTemplate += `<head><meta charset="UTF-8"><!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet><x:Name>Detalle Facturación</x:Name><x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions></x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]--></head><body>`;
        excelTemplate += `<table border="1">`;

        // 2. Extraemos los encabezados de la tabla (.tabla-detalle)
        const cabeceras = contenedorModal.querySelectorAll(".tabla-detalle thead th");
        excelTemplate += `<tr style="background-color: #1565C0; color: #FFFFFF; font-weight: bold;">`;
        cabeceras.forEach(th => {
            excelTemplate += `<td>${th.innerText.trim()}</td>`;
        });
        excelTemplate += `</tr>`;

        // 3. Extraemos el universo completo de filas (vayan 20 o 100 registros)
        const filas = contenedorModal.querySelectorAll(".tabla-detalle tbody tr");
        if (filas.length === 0) {
            alert("No hay registros en la tabla para exportar.");
            return;
        }

        filas.forEach(fila => {
            excelTemplate += `<tr>`;
            const celdas = fila.querySelectorAll("td");
            celdas.forEach(td => {
                let valorCelda = td.innerText.trim();
                
                // Limpieza de caracteres de moneda para que Excel interprete los números nativamente
                if (valorCelda.includes('$')) {
                    valorCelda = valorCelda.replace('$', '').replace(/\./g, '').trim();
                }
                excelTemplate += `<td>${valorCelda}</td>`;
            });
            excelTemplate += `</tr>`;
        });

        excelTemplate += `</table></body></html>`;

        // 4. Creamos el objeto Binario (Blob) de descarga instantánea
        const blob = new Blob([excelTemplate], { type: "application/vnd.ms-excel" });
        const url = URL.createObjectURL(blob);
        const linkTemporal = document.createElement("a");
        
        linkTemporal.href = url;
        linkTemporal.download = `Detalle_Facturacion_Modal.xls`;
        document.body.appendChild(linkTemporal);
        linkTemporal.click();
        
        // Limpieza de memoria
        document.body.removeChild(linkTemporal);
        URL.revokeObjectURL(url);
        console.log("-> Archivo de facturación del modal exportado con éxito.");
    }
});