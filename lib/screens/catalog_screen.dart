import 'package:flutter/material.dart';
import '../services/api_service.dart';

class CatalogScreen extends StatefulWidget {
  const CatalogScreen({Key? key}) : super(key: key);

  @override
  _CatalogScreenState createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> {
  final ApiService _apiService = ApiService();
  final TextEditingController _searchController = TextEditingController();
  
  String _searchQuery = "";
  int? _selectedThickness;
  late Future<List<dynamic>> _productsFuture;
  late Future<List<dynamic>> _hitsFuture;

  @override
  void initState() {
    super.initState();
    _refreshData();
  }

  void _refreshData() {
    setState(() {
      _productsFuture = _apiService.searchProducts(_searchQuery, thickness: _selectedThickness);
      _hitsFuture = _apiService.getTopSellers();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text('Склад и Хиты'),
        backgroundColor: Colors.brown[800],
      ),
      body: Column(
        children: [
          // 1. ПОИСК И ФИЛЬТРЫ
          Container(
            padding: const EdgeInsets.all(12),
            color: Colors.white,
            child: Column(
              children: [
                TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    hintText: 'Поиск декора (напр. Белый, Дуб)...',
                    prefixIcon: const Icon(Icons.search),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.clear),
                      onPressed: () {
                        _searchController.clear();
                        _searchQuery = "";
                        _refreshData();
                      },
                    ),
                  ),
                  onChanged: (value) {
                    _searchQuery = value;
                    _refreshData();
                  },
                ),
                const SizedBox(height: 10),
                // Быстрые фильтры по толщине
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [10, 16, 18, 22].map((mm) {
                    return ChoiceChip(
                      label: Text('$mm мм'),
                      selected: _selectedThickness == mm,
                      selectedColor: Colors.brown[300],
                      onSelected: (selected) {
                        setState(() {
                          _selectedThickness = selected ? mm : null;
                          _refreshData();
                        });
                      },
                    );
                  }).toList(),
                ),
              ],
            ),
          ),

          Expanded(
            child: ListView(
              children: [
                // 2. БЛОК ХИТЫ ПРОДАЖ (Горизонтальный)
                const Padding(
                  padding: EdgeInsets.all(12),
                  child: Text('🔥 ХИТЫ РАСПИЛА', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ),
                SizedBox(
                  height: 120,
                  child: FutureBuilder<List<dynamic>>(
                    future: _hitsFuture,
                    builder: (context, snapshot) {
                      if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
                      return ListView.builder(
                        scrollDirection: Axis.horizontal,
                        itemCount: snapshot.data!.length,
                        itemBuilder: (context, index) {
                          final item = snapshot.data![index];
                          return Container(
                            width: 160,
                            margin: const EdgeInsets.only(left: 12),
                            decoration: BoxDecoration(
                              color: Colors.orange[50],
                              borderRadius: BorderRadius.circular(15),
                              border: Border.all(color: Colors.orange[200]!),
                            ),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Text(item['name'], textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.bold)),
                                const SizedBox(height: 5),
                                Text('Продано: ${item['sales_count']}', style: const TextStyle(color: Colors.deepOrange)),
                              ],
                            ),
                          );
                        },
                      );
                    },
                  ),
                ),

                // 3. ОСНОВНОЙ КАТАЛОГ СКЛАДА
                const Padding(
                  padding: EdgeInsets.all(12),
                  child: Text('📦 ВЕСЬ СКЛАД', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                ),
                FutureBuilder<List<dynamic>>(
                  future: _productsFuture,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState == ConnectionState.waiting) return const Center(child: CircularProgressIndicator());
                    if (snapshot.hasError) return Center(child: Text('Ошибка сервера'));
                    
                    final products = snapshot.data ?? [];
                    return ListView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: products.length,
                      itemBuilder: (context, index) {
                        final p = products[index];
                        return Card(
                          margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
                          child: ListTile(
                            title: Text(p['name'], style: const TextStyle(fontWeight: FontWeight.bold)),
                            subtitle: Text('Толщина: ${p['thickness']} мм | Категория: ${p['category']}'),
                            trailing: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                Text('Свободно: ${p['stock']}', style: const TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
                                Text('Занято: ${p['reserved']}', style: const TextStyle(color: Colors.red, fontSize: 12)),
                              ],
                            ),
                          ),
                        );
                      },
                    );
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
