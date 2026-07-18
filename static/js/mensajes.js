function mostrarMensaje(tipo, titulo, mensaje) {

    Swal.fire({
        icon: tipo,
        title: titulo,
        text: mensaje,
        confirmButtonText: "Aceptar",
        confirmButtonColor: "#1D5FB8",
        allowOutsideClick: false,
        allowEscapeKey: true,
        heightAuto: false
    });
}

const Mensajes = {

    info(texto, titulo = "Información") {
        Swal.fire({
            icon: "info",
            title: titulo,
            text: texto,
            confirmButtonText: "Aceptar",
            confirmButtonColor: "#1D5FB8",
            allowOutsideClick: false,
            heightAuto: false
        });
    },

    warning(texto, titulo = "Advertencia") {
        Swal.fire({
            icon: "warning",
            title: titulo,
            text: texto,
            confirmButtonText: "Aceptar",
            confirmButtonColor: "#D97706",
            allowOutsideClick: false,
            heightAuto: false
        });
    },

    error(texto, titulo = "Error") {
        Swal.fire({
            icon: "error",
            title: titulo,
            text: texto,
            confirmButtonText: "Aceptar",
            confirmButtonColor: "#DC2626",
            allowOutsideClick: false,
            heightAuto: false
        });
    },

    success(texto, titulo = "Proceso completado") {
        Swal.fire({
            icon: "success",
            title: titulo,
            text: texto,
            confirmButtonText: "Aceptar",
            confirmButtonColor: "#15803D",
            allowOutsideClick: false,
            heightAuto: false
        });
    },

    movil(texto, titulo = "Archivo no válido") {

        Swal.fire({
            icon: "warning",
            title: titulo,
            text: texto,
            confirmButtonText: "Aceptar",
            confirmButtonColor: "#1565C0",
            allowOutsideClick: false,
            allowEscapeKey: true,
            heightAuto: false
        });
    }
};