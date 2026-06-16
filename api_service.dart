// Добавьте этот метод в существующий класс ApiService в файле lib/services/api_service.dart

Future<List<dynamic>> getTopSellers() async {
  try {
    final response = await _dio.get('$baseUrl/products/top-sellers');
    return response.data;
  } catch (e) {
    throw Exception('Ошибка загрузки хитов продаж: $e');
  }
}
