/**
 * Punto unico donde vive la direccion del backend.
 *
 * Antes estaba escrita a mano ("http://127.0.0.1:8000") en cada fetch y
 * en cada <img>. Eso funciona exactamente hasta el momento de desplegar:
 * el navegador del jurado no tiene un FastAPI corriendo en su localhost.
 *
 * PUBLIC_ es obligatorio en SvelteKit para las variables que el codigo
 * del navegador puede leer. Todo lo que no lleve ese prefijo se queda en
 * el servidor — que es justo lo que quieres para las credenciales.
 */
import { PUBLIC_API_URL } from '$env/static/public';

export const API_BASE = PUBLIC_API_URL || 'http://127.0.0.1:8000';

/** Construye una ruta de API: api('/api/alerta/estado') */
export const api = (ruta: string) => `${API_BASE}${ruta}`;

/**
 * Convierte la url relativa que devuelve el backend ("/static/mapas/X.png")
 * en absoluta. Devuelve null si no hay mapa, para que el componente pueda
 * distinguir "no generado" de "url vacia".
 */
export const assetUrl = (ruta: string | null | undefined): string | null =>
	ruta ? `${API_BASE}${ruta}` : null;

/**
 * fetch con mensaje de error util.
 *
 * Un `catch` que solo dice "Error fetching data" oculta la diferencia
 * entre "el backend no esta levantado", "devolvio 500" y "CORS lo
 * bloqueo". Son tres problemas distintos con tres arreglos distintos.
 */
export async function getJSON<T>(ruta: string): Promise<T> {
	let res: Response;
	try {
		res = await fetch(api(ruta));
	} catch {
		throw new Error(
			`No se pudo contactar con el backend en ${API_BASE}. ` +
				`¿Está corriendo (python main.py)?`
		);
	}
	if (!res.ok) {
		throw new Error(`El backend respondió ${res.status} en ${ruta}.`);
	}
	return (await res.json()) as T;
}