document.addEventListener("DOMContentLoaded", () => {

    console.log("negociacion.js cargado");    
    console.log("Filtros KPI:", filtrosKPI);

    // ==============================================================
    // VALIDACIÓN DE ARCHIVOS DESDE DRIVE EN MÓVILES (CORREGIDO)
    // ==============================================================
    const inputArchivoNegociacion = document.getElementById("archivoExcelNegociacion") || document.querySelector('input[type="file"]');

    if (inputArchivoNegociacion) {
        inputArchivoNegociacion.addEventListener("change", function (evento) {
            const archivo = evento.target.files[0];
            
            if (!archivo) return;

            console.log("-> Archivo cargado. Nombre:", archivo.name, "| Tamaño:", archivo.size);

            // Validamos si el archivo proviene de un URI virtual de Drive (típico en Android/iOS)
            // O si el tamaño reportado es 0 bytes o el nombre tiene extensiones temporales de la nube
            const esDesdeDrive = archivo.name.includes(".driveextension") || 
                                archivo.name.startsWith("content://") || 
                                archivo.size === 0;

            if (esDesdeDrive) {
                // Detenemos cualquier procesamiento del navegador para evitar que cierre la página
                evento.preventDefault();
                evento.stopPropagation();
                this.value = ""; // Limpiamos el input para proteger el sistema

                console.log("-> Intento de carga detectado desde Drive en dispositivo móvil. Bloqueando...");

                // Invocamos tu mensaje modular nativo de SweetAlert2 de forma controlada
                if (typeof Mensajes !== "undefined" && typeof Mensajes.movil === "function") {
                    Mensajes.movil(
                        "No es posible cargar archivos directamente desde Google Drive en dispositivos móviles. Por favor, descargue el archivo Excel a la memoria interna de su dispositivo e inténtelo nuevamente.",
                        "Archivo no válido"
                    );
                } else if (typeof Swal !== "undefined") {
                    Swal.fire({
                        icon: "warning",
                        title: "Archivo no válido",
                        text: "No es posible cargar archivos directamente desde Google Drive en dispositivos móviles. Descárguelo a la memoria local.",
                        confirmButtonText: "Aceptar",
                        confirmButtonColor: "#1565C0",
                        allowOutsideClick: false,
                        heightAuto: false
                    });
                }
            }
        });
    }


    const hojas = document.querySelectorAll(".item-hoja");

    hojas.forEach(item => {

        item.addEventListener("click", () => {

            // Quitar selección anterior
            hojas.forEach(h =>
                h.classList.remove("seleccionada")
            );

            // Marcar la actual
            item.classList.add("seleccionada");

            // Marcar el radio
            const radio = item.querySelector("input[type='radio']");
            if (radio) {
                radio.checked = true;
            }

        });

    });

});

$(document).ready(function () {

    if (!$("#tablaNegociacion").length) return;

    console.log("jQuery:", typeof $);
    console.log("DataTable:", typeof DataTable);

    const tabla = $("#tablaNegociacion").DataTable({

        pageLength:15,
        ordering:true,
        searching:true,
        paging:true,
        info:false,
        lengthChange:false,
        autoWidth:false,
        responsive:false,

        columnDefs: [

            {
                targets: [
                    columnasMoneda = 2, // VALOR OFERTADO
                    3,                  // REGULACION
                    4,                  // NT
                    5,                  // REFERENCIA
                    6,                  // PM
                    7,                  // VALOR OBJETIVO
                ],

                className: "text-end",

                render: function (data, type) {

                    if (type !== "display")
                        return data;

                    if (data === null || data === "" || data === undefined)
                        return "";

                    let valor = parseFloat(
                        String(data)
                            .replace(/\./g, "")
                            .replace(",", ".")
                    );

                    if (isNaN(valor))
                        return data;

                    return valor.toLocaleString("es-CO", {
                        style: "currency",
                        currency: "COP",
                        minimumFractionDigits: 0,
                        maximumFractionDigits: 2
                    });

                }

            }

        ],

        dom:"rtp",

        language:{
            zeroRecords:"No se encontraron resultados",

            paginate:{
                previous:"◀",
                next:"▶"
            }
        }

    });

    console.log("DataTable inicializada");

    const columnas = {};

    tabla.columns().every(function(i){

        columnas[
            $(tabla.column(i).header()).text().trim().toUpperCase()
        ] = i;

    });

    function limpiarFiltros() {

        tabla.search("");
        tabla.columns().search("").draw();

    }

    function aplicarFiltro(columna, valores) {

        const indice = columnas[columna.toUpperCase()];

        if (indice === undefined) return;

        const regex = valores

            .map(v => "^" + v.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "$")

            .join("|");

        tabla

            .column(indice)

            .search(regex, true, false)

            .draw();
    }

    function activarFiltro(nombreFiltro){

        limpiarFiltros();

        if(nombreFiltro==="todos"){

            $(".indicador-card").removeClass("activo");

            $("#filtroTabla").val("todos");

            return;

        }

        const filtro=filtrosKPI[nombreFiltro];

        if(!filtro){
            console.warn("Filtro inexistente:",nombreFiltro);
            return;
        }

        aplicarFiltro(
            filtro.columna,
            filtro.valores
        );

        $(".indicador-card").removeClass("activo");

        $('.indicador-card[data-filtro="'+nombreFiltro+'"]')
            .addClass("activo");

        const mapaCombo = {
            aceptables: "ACEPTAR",
            renegociar: "RENEGOCIAR",
            duplicados: "DUPLICADO",
            activos: "ACTIVO",
            no_activos: "NO ACTIVO",
            registros: "todos"
        };

        $("#filtroTabla").val(mapaCombo[nombreFiltro] || "todos");
    }

    $("#buscarTabla").on("keyup", function () {

        tabla.search(this.value).draw();
    });

    tabla.on("draw", function(){
        $("#contadorRegistros").text(
            tabla.rows({search:"applied"}).count()+" registros"
        );
    });

    const mapaFiltros={
        "ACEPTAR":"aceptables",
        "RENEGOCIAR":"renegociar",
        "DUPLICADO":"duplicados",
        "ACTIVO":"activos",
        "NO ACTIVO":"no_activos"
    };    

    $("#filtroTabla").on("change",function(){

        const valor=this.value;

        if(valor==="todos"){

            activarFiltro("todos");
            return;
        }
        activarFiltro(mapaFiltros[valor]);
    });

    $(".indicador-card[data-filtro]").on("click",function(){

        activarFiltro(
            $(this).data("filtro")
        );
    });

    $(function () {

        $("#toggleValidacion").on("click", function () {

            $("#contenidoValidacion").stop(true, true).slideToggle(250);

            $("#iconoToggleValidacion").text(function (_, t) {
                return t === "▲" ? "▼" : "▲";
            });

        });

    });

    $("#toggleHojas").on("click", function () {

        // Oculta / muestra el contenido del panel
        $("#contenidoHojas").stop(true, true).slideToggle(250);

        // Cambia la flecha
        $("#iconoToggleHojas").text(function (_, t) {
            return t === "▲" ? "▼" : "▲";
        });

        // Expande o contrae la tabla
        $("#panelTabla").toggleClass("expandida");

    });

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

// ==============================================================
// BLINDAJE DE SEGURIDAD PARA ENVÍO DE ARCHIVOS (FORM SUBMIT)
// ==============================================================
document.addEventListener("DOMContentLoaded", function() {
    // Buscamos el formulario de cambio de archivo usando su clase nativa
    const formCambiar = document.querySelector(".form-cambiar");

    if (formCambiar) {
        formCambiar.addEventListener("submit", function (evento) {
            // Buscamos el input file dentro de este formulario
            const inputFile = this.querySelector('input[type="file"]');
            
            if (inputFile && inputFile.files && inputFile.files.length > 0) {
                const archivo = inputFile.files[0];
                console.log("-> Git interceptando Submit. Archivo a enviar:", archivo.name, "| Tamaño:", archivo.size);

                // Criterios estrictos para identificar un archivo virtual de Google Drive en celulares
                const esDesdeDrive = archivo.name.includes(".driveextension") || 
                                     archivo.name.startsWith("content://") || 
                                     archivo.size === 0;

                if (esDesdeDrive) {
                    // FRENAMOS EN SECO EL SUBMIT ANTES DE QUE VIAJE A FLASK
                    evento.preventDefault();
                    evento.stopPropagation();
                    
                    inputFile.value = ""; // Vaciamos el campo por seguridad
                    console.warn("-> Envío cancelado: El archivo proviene de Google Drive Móvil.");

                    // Disparamos tu alerta corporativa de SweetAlert2
                    if (typeof Mensajes !== "undefined" && typeof Mensajes.movil === "function") {
                        Mensajes.movil(
                            "No es posible procesar archivos directamente desde Google Drive en dispositivos móviles. Por favor, descargue el documento Excel a la memoria interna de su teléfono e inténtelo nuevamente.",
                            "Archivo no válido"
                        );
                    } else if (typeof Swal !== "undefined") {
                        Swal.fire({
                            icon: "warning",
                            title: "Archivo no válido",
                            text: "No es posible procesar archivos directamente desde Google Drive en dispositivos móviles. Descárguelo a la memoria local.",
                            confirmButtonText: "Aceptar",
                            confirmButtonColor: "#1565C0",
                            allowOutsideClick: false,
                            heightAuto: false
                        });
                    }
                } else {
                    // SI EL ARCHIVO ES VÁLIDO (PC o Memoria Local Móvil):
                    // Lanzamos el spinner para dar excelente feedback visual mientras Flask procesa
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
                    console.log("-> Archivo verificado. Permitiendo viaje síncrono a Flask con éxito.");
                }
            }
        });
    }
});