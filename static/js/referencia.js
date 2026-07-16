document.addEventListener("DOMContentLoaded", function () {
    const radios = document.querySelectorAll('input[name="tipo_filtro"]');
    const busquedaTexto = document.getElementById("busquedaTexto");
    const busquedaRegional = document.getElementById("busquedaRegional");
    const lblCriterio = document.getElementById("lblCriterio");

    // Validamos la existencia para evitar que el script falle y congele el formulario
    const inputTexto = busquedaTexto ? busquedaTexto.querySelector('input[type="text"]') : null;
    const selectRegional = busquedaRegional ? busquedaRegional.querySelector('select') : null;

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

    // Vinculamos los eventos de manera segura
    if (radios.length > 0) {
        radios.forEach(radio => radio.addEventListener("change", alternarBuscadores));
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

// Función global para controlar el cierre del modal
function cerrarElModalNativo() {
    const modal = document.getElementById('modalDetalleFacturacion');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restaura el scroll del fondo
    }
}

// Inicialización de escuchadores de eventos al cargar el DOM
document.addEventListener('DOMContentLoaded', function() {
    const btnDetalle = document.getElementById("btnDetalle");
    const modal = document.getElementById('modalDetalleFacturacion');
    const modalContent = document.getElementById('modalBodyContent');

    if (btnDetalle) {
        btnDetalle.addEventListener("click", function (evento) {
            evento.preventDefault();
            
            const codigo = this.getAttribute('data-cum');
            console.log("Iniciando apertura modular para el CUM:", codigo);

            if (!codigo || codigo.trim() === "") {
                alert("Por favor, seleccione un medicamento primero.");
                return;
            }

            if (!modal || !modalContent) {
                console.error("No se encontraron los contenedores del modal.");
                return;
            }

            // Petición AJAX limpia a Flask
            fetch("/detalle/" + encodeURIComponent(codigo.trim()), {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(response => {
                if (!response.ok) throw new Error("Error en servidor Flask: " + response.status);
                return response.text();
            })
            .then(html => {
                // Inyectamos la respuesta renderizada de Flask
            modalContent.innerHTML = html;
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden'; 

            // Vinculamos la X de cierre
            const btnCerrar = document.getElementById('btnCerrarModal');
            if (btnCerrar) {
                btnCerrar.addEventListener('click', cerrarElModalNativo);
            }

            setTimeout(() => {
                const filas = modalContent.querySelectorAll(".tabla-detalle tbody tr");
                const registrosPorPagina = 20;
                let paginaActual = 1;
                const totalRegistros = filas.length;
                const totalPaginas = Math.ceil(totalRegistros / registrosPorPagina);

                // --- LÓGICA DE EXPORTACIÓN A EXCEL DESDE EL MODAL ---
                const btnExportar = document.getElementById("btnExportarExcelModal");
                if (btnExportar) {
                    btnExportar.addEventListener("click", function () {
                        // Construimos la estructura básica de una tabla en formato XML para Excel
                        let excelTemplate = `<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://w3.org">`;
                        excelTemplate += `<head><meta charset="UTF-8"><!--[if gte mso 9]><xml><x:ExcelWorkbook><x:ExcelWorksheets><x:ExcelWorksheet><x:Name>Detalle Facturación</x:Name><x:WorksheetOptions><x:DisplayGridlines/></x:WorksheetOptions></x:ExcelWorksheet></x:ExcelWorksheets></x:ExcelWorkbook></xml><![endif]--></head><body>`;
                        excelTemplate += `<table border="1">`;

                        // 1. Extraemos los encabezados de la tabla (thead)
                        const cabeceras = modalContent.querySelectorAll(".tabla-detalle thead th");
                        excelTemplate += `<tr style="background-color: #1565C0; color: #FFFFFF; font-weight: bold;">`;
                        cabeceras.forEach(th => {
                            excelTemplate += `<td>${th.innerText.trim()}</td>`;
                        });
                        excelTemplate += `</tr>`;

                        // 2. Extraemos TODAS las filas de datos (ignorando si están ocultas por el paginado)
                        filas.forEach(fila => {
                            excelTemplate += `<tr>`;
                            const celdas = fila.querySelectorAll("td");
                            celdas.forEach(td => {
                                let valorCelda = td.innerText.trim();
                                
                                // Si la celda contiene valores financieros (ej: $15.000), limpiamos los símbolos para Excel
                                if (valorCelda.startsWith('$')) {
                                    valorCelda = valorCelda.replace('$', '').replace(/\./g, '').trim();
                                }
                                excelTemplate += `<td>${valorCelda}</td>`;
                            });
                            excelTemplate += `</tr>`;
                        });

                        excelTemplate += `</table></body></html>`;

                        // Generamos el Blob de descarga y disparamos el archivo Excel
                        const blob = new Blob([excelTemplate], { type: "application/vnd.ms-excel" });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        
                        // Extraemos el código CUM para ponerlo de nombre al archivo de forma inteligente
                        const cumArchivo = codigo || "Detalle_Facturacion";
                        a.href = url;
                        a.download = `Detalle_Facturacion_${cumArchivo}.xls`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                    });
                }

                // --- LOGICA DE PAGINACIÓN EXISTENTE (MANTENER IGUAL) ---
                if (totalRegistros > registrosPorPagina) {
                    const bloquePag = document.getElementById("paginacionModalBloque");
                    if (bloquePag) bloquePag.style.display = "flex";

                    function actualizarTablaModal() {
                        const inicio = (paginaActual - 1) * registrosPorPagina;
                        const fin = inicio + registrosPorPagina;

                        filas.forEach((fila, indice) => {
                            fila.style.display = (indice >= inicio && indice < fin) ? "" : "none";
                        });

                        const txtInfo = document.getElementById("infoPaginacionModal");
                        if (txtInfo) {
                            txtInfo.textContent = `Mostrando registros del ${inicio + 1} al ${Math.min(fin, totalRegistros)} de ${totalRegistros}`;
                        }

                        document.getElementById("btnPrevModal").disabled = (paginaActual === 1);
                        document.getElementById("btnNextModal").disabled = (paginaActual === totalPaginas);
                    }

                    const btnPrev = document.getElementById("btnPrevModal");
                    const btnNext = document.getElementById("btnNextModal");
                    btnPrev.replaceWith(btnPrev.cloneNode(true));
                    btnNext.replaceWith(btnNext.cloneNode(true));

                    document.getElementById("btnPrevModal").addEventListener("click", () => {
                        if (paginaActual > 1) {
                            paginaActual--;
                            actualizarTablaModal();
                            const tablaContenedor = document.querySelector(".detalle-tabla");
                            if (tablaContenedor) tablaContenedor.scrollTop = 0;
                        }
                    });

                    document.getElementById("btnNextModal").addEventListener("click", () => {
                        if (paginaActual < totalPaginas) {
                            paginaActual++;
                            actualizarTablaModal();
                            const tablaContenedor = document.querySelector(".detalle-tabla");
                            if (tablaContenedor) tablaContenedor.scrollTop = 0;
                        }
                    });

                    actualizarTablaModal();
                } else {
                    const bloquePag = document.getElementById("paginacionModalBloque");
                    if (bloquePag) bloquePag.style.display = "none";
                }
            }, 50);

            })
            .catch(error => {
                console.error("Error al cargar el modal:", error);
                alert("Ocurrió un error al cargar el detalle de facturación.");
            });
        });
    }

    // Cierra el modal al hacer clic en la capa oscura difuminada de fondo
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                cerrarElModalNativo();
            }
        });
    }
});

