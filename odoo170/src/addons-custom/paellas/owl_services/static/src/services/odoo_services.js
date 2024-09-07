/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { Dialog } from "@web/core/dialog/dialog";
import { Layout } from "@web/search/layout";

const jsQR = window.jsQR;  // Asegúrate de que jsQR esté cargado globalmente

// Definir el componente OdooServices
class OdooServices extends Component {
    static template = "owl_services.OdooServices";
    static components = { Layout };

    constructor() {
        super(...arguments);
        this.state = {
            barcodeValue: "",
            isBarcodeRead: false
        };
        this.fetchBarcodeValue();
    }

    async fetchBarcodeValue() {
        // Lógica para obtener el valor del código de barras desde el backend
        console.log("Iniciando fetchBarcodeValue...");
        try {
            const routeValue = '/api/barcode/process';
            const response = await fetch(routeValue, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.env.services.csrfToken
                },
                body: JSON.stringify({
                    barcode_data: {
                        model: 'custom.barcode.model',
                        method: 'process',
                        args: []
                    }
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log("Respuesta obtenida del servidor:", data);
            if (data.error) {
                console.error("Error:", data.error);
            } else {
                this.state.barcodeValue = data.barcode_value || "No barcode value";
                this.render();  // Actualiza la vista para mostrar el valor del código de barras
            }

        } catch (error) {
            console.error("Error al obtener el valor del código QR:", error);
        }
    }

    async callBarcodeService() {
        let video = document.createElement('video');
        video.setAttribute('id', 'barcode_id');

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;

            // Esperar a que se cargue el video y sus metadatos
            video.addEventListener('loadedmetadata', () => {
                video.play();

                const dialogService = this.env.services.dialog;
                dialogService.add(Dialog, {
                    title: 'Escáner de Código QR',
                    buttons: [{
                        text: 'Cerrar',
                        classes: 'btn-primary',
                        close: true,
                        click: () => {
                            let tracks = video.srcObject.getTracks();
                            tracks.forEach(track => track.stop());
                        }
                    }],
                    size: 'medium',
                    $content: video,
                });

                // Iniciar el escaneo después de que el video esté listo
                this.scanQRCode(video);
            });
        } catch (error) {
            console.error("Error al acceder a la cámara:", error);
        }
    }

    // Función para escanear códigos QR usando jsQR
    scanQRCode(video) {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');

        const scan = () => {
            if (!this.state.isBarcodeRead) {
                // Asegurarse de que el video tenga dimensiones antes de obtener la imagen
                if (video.videoWidth > 0 && video.videoHeight > 0) {
                    canvas.width = video.videoWidth;
                    canvas.height = video.videoHeight;
                    context.drawImage(video, 0, 0, canvas.width, canvas.height);

                    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
                    const qrCode = jsQR(imageData.data, canvas.width, canvas.height);

                    if (qrCode) {
                        console.log("Código QR leído:", qrCode.data);
                        this.updateBarcodeField(qrCode.data);
                        this.state.isBarcodeRead = true;
                        let tracks = video.srcObject.getTracks();
                        tracks.forEach(track => track.stop());
                    } else {
                        requestAnimationFrame(scan);
                    }
                } else {
                    // Si las dimensiones no están listas, intentar nuevamente en el próximo frame
                    requestAnimationFrame(scan);
                }
            }
        };

        requestAnimationFrame(scan);
    }

    async updateBarcodeField(barcodeValue) {
        console.log("Iniciando updateBarcodeField con barcodeValue:", barcodeValue);
        this.state.barcodeValue = barcodeValue;

        try {
            const routeValue = '/api/barcode/process';
            const response = await fetch(routeValue, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.env.services.csrfToken
                },
                body: JSON.stringify({
                    barcode_data: {
                        model: 'custom.barcode.model',
                        method: 'process',
                        args: [{ barcode_value: barcodeValue }]
                    }
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log("Respuesta del servidor:", data);

            if (data.error) {
                console.error("Error del servidor:", data.error);
            } else {
                console.log("Datos procesados correctamente:", data.data);
                this.render();
            }

        } catch (error) {
            console.error("Error al procesar el valor del código QR:", error);
        }
    }
}

// Registrar el componente en el registro de Odoo
registry.category("actions").add("owl_services.OdooServices", OdooServices);
