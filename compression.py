from PIL import Image
import numpy as np
import pywt
from sklearn.cluster import KMeans
from io import BytesIO


# JPEG сжатие
def jpeg_compression(image, quality=50):
    """Сжатие изображения методом JPEG"""
    try:
        # Конвертируем в RGB если нужно
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Сохраняем в буфер с JPEG сжатием
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)

        # Создаем сжатое изображение
        compressed_image = Image.open(buffer)
        return compressed_image
    except Exception as e:
        raise Exception(f"Ошибка JPEG сжатия: {str(e)}")


# Вейвлет сжатие (упрощенная версия)
def wavelet_compression(image, compression_ratio=0.1):
    """Сжатие изображения методом вейвлет-преобразования"""
    try:
        # Конвертируем в numpy array
        img_array = np.array(image)

        if len(img_array.shape) == 3:
            compressed_channels = []
            for i in range(3):
                # Применяем вейвлет-преобразование
                coeffs = pywt.wavedec2(img_array[:, :, i], "db1", level=3)

                # Сжимаем коэффициенты
                coeffs_arr, coeff_slices = pywt.coeffs_to_array(coeffs)

                # Пороговая обработка для сжатия
                threshold = np.percentile(
                    np.abs(coeffs_arr), 100 * (1 - compression_ratio)
                )
                coeffs_arr[np.abs(coeffs_arr) < threshold] = 0

                # Восстанавливаем коэффициенты
                coeffs = pywt.array_to_coeffs(
                    coeffs_arr, coeff_slices, output_format="wavedec2"
                )

                # Обратное вейвлет-преобразование
                compressed_channel = pywt.waverec2(coeffs, "db1")
                compressed_channels.append(compressed_channel)

            # Объединяем каналы
            compressed_array = np.stack(compressed_channels, axis=2)
            compressed_array = np.clip(compressed_array, 0, 255).astype(np.uint8)
        else:
            # Для grayscale изображений
            coeffs = pywt.wavedec2(img_array, "db1", level=3)
            coeffs_arr, coeff_slices = pywt.coeffs_to_array(coeffs)

            threshold = np.percentile(np.abs(coeffs_arr), 100 * (1 - compression_ratio))
            coeffs_arr[np.abs(coeffs_arr) < threshold] = 0

            coeffs = pywt.array_to_coeffs(
                coeffs_arr, coeff_slices, output_format="wavedec2"
            )
            compressed_array = pywt.waverec2(coeffs, "db1")
            compressed_array = np.clip(compressed_array, 0, 255).astype(np.uint8)

        return Image.fromarray(compressed_array)
    except Exception as e:
        raise Exception(f"Ошибка вейвлет сжатия: {str(e)}")


# Квантование цветов
def color_quantization_simple(image, n_colors=16):
    """Квантование цвета"""
    try:
        # Конвертируем в numpy array
        img_array = np.array(image)

        # Изменяем форму для кластеризации
        h, w, c = img_array.shape
        img_reshaped = img_array.reshape(-1, 3)

        # Применяем K-means для уменьшения количества цветов
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        labels = kmeans.fit_predict(img_reshaped)

        # Восстанавливаем изображение с уменьшенной палитрой
        compressed_array = kmeans.cluster_centers_[labels].reshape(h, w, c)
        compressed_array = np.clip(compressed_array, 0, 255).astype(np.uint8)

        return Image.fromarray(compressed_array)
    except Exception as e:
        raise Exception(f"Ошибка сжатия: {str(e)}")
