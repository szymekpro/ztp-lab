import { useEffect, useMemo, useState } from "react";

import { apiGet, apiPost } from "../api/client";
import Navbar from "../components/Navbar";
import useCurrentOperator from "../hooks/useCurrentOperator";

function ProductsPage() {
  const { authLoading, authError } = useCurrentOperator();

  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState(null);

  const [selectedCategory, setSelectedCategory] = useState("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [quantities, setQuantities] = useState({});
  const [addedIds, setAddedIds] = useState({});

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadData() {
    try {
      const productsData = await apiGet("/api/v1/product/products");
      const cartData = await apiGet("/api/v1/cart");

      setProducts(productsData.items ? productsData.items : productsData);
      setCart(cartData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!authLoading && !authError) {
      loadData();
    }
  }, [authLoading, authError]);

  const categories = useMemo(() => {
    if (!Array.isArray(products)) return [];
    return [
      ...new Set(
        products.map((product) => product.category?.name).filter(Boolean)
      ),
    ];
  }, [products]);

  const filteredProducts = useMemo(() => {
    if (!Array.isArray(products)) return [];
    return products.filter((product) => {
      const matchCat =
        selectedCategory === "ALL" ||
        product.category?.name === selectedCategory;
      const matchSearch =
        searchQuery === "" ||
        product.name.toLowerCase().includes(searchQuery.toLowerCase());
      return matchCat && matchSearch;
    });
  }, [products, selectedCategory, searchQuery]);

  function handleCategoryChange(event) {
    setSelectedCategory(event.target.value);
  }

  function handleSearchChange(event) {
    setSearchQuery(event.target.value);
  }

  function handleQuantityChange(productId, value) {
    setQuantities(prev => ({ ...prev, [productId]: parseInt(value) || 1 }));
  }

  async function handleAddToCart(product) {
    setError("");
    const qty = quantities[product.id] || 1;

    try {
      const cartItem = cart?.items?.find(item => item.product.id === product.id);

      if (cartItem) {
        await updateCartApi(product, cartItem, qty);
      } else {
        await apiPost("/api/v1/cart/items", {
          product_id: product.id,
          quantity: qty,
        });
      }

      setAddedIds(prev => ({ ...prev, [product.id]: true }));
      setTimeout(() => {
         setAddedIds(prev => ({ ...prev, [product.id]: false }));
      }, 2000);

      await loadData();
    } catch (err) {
      setError(err.message);
      // Fade out error after a few seconds so it doesn't linger forever
      setTimeout(() => setError(""), 5000);
    }
  }
  
  async function updateCartApi(product, cartItem, addQty) {
    const apiPatch = (await import("../api/client")).apiPatch;
    await apiPatch("/api/v1/cart/items/" + cartItem.id, {
        quantity: cartItem.quantity + addQty,
    });
  }

  if (authLoading) {
    return (
      <main className="page">
        <section className="card">
          <p>Sprawdzanie sesji...</p>
        </section>
      </main>
    );
  }

  if (authError) {
    return null;
  }

  return (
    <>
      <Navbar />

      <main className="products-layout">
        <aside className="filters-panel">
          <h2>Filtry</h2>

          <label>
            Kategoria
            <select value={selectedCategory} onChange={handleCategoryChange}>
              <option value="ALL">Wszystkie</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </label>
          
          <label style={{ marginTop: '16px', display: 'block' }}>
            Producent / Nazwa
            <input 
              type="text"
              value={searchQuery}
              onChange={handleSearchChange}
              placeholder="Szukaj..."
              style={{ width: '100%', marginTop: '6px', padding: '6px', boxSizing: 'border-box' }}
            />
          </label>
        </aside>

        <section className="products-content">
          <h1>Lista produktow</h1>

          {loading && <p>Ladowanie produktow...</p>}

          {error && <div style={{ background: '#ffecec', color: '#c0392b', padding: '10px', borderRadius: '8px', marginBottom: '16px', border: '1px solid #c0392b' }}>
            <strong>Błąd:</strong> {error}
          </div>}

          {!loading && Array.isArray(products) && (
            <>
              <p>
                Wyswietlono: {filteredProducts.length} z {products.length}
              </p>

              <div className="product-list">
                {filteredProducts.map((product) => {
                  const qty = quantities[product.id] || 1;
                  const isOutOfStock = product.quantity <= 0;
                  const justAdded = addedIds[product.id];

                  return (
                    <article key={product.id} className="product-item">
                      <div>
                        <strong>
                          {product.name}
                        </strong>

                        <p>Cena: {product.price} zł</p>
                        <p>Dostępność: {product.quantity} szt.</p>
                        <p>Kategoria: {product.category?.name}</p>
                      </div>
                      
                      <div style={{ marginTop: '10px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <input 
                          type="number" 
                          min="1" 
                          max={product.quantity} 
                          value={qty} 
                          onChange={(e) => handleQuantityChange(product.id, e.target.value)} 
                          style={{ width: '55px', padding: '8px 4px', textAlign: 'center', borderRadius: '6px', border: '1px solid #ccc' }}
                          disabled={isOutOfStock}
                        />
                        <button
                          disabled={isOutOfStock}
                          onClick={() => handleAddToCart(product)}
                          style={{ margin: 0, alignSelf: 'center' }}
                          className={justAdded ? "added-button" : ""}
                        >
                          {isOutOfStock ? "Brak na stanie" : (justAdded ? "Dodano!" : "Dodaj do koszyka")}
                        </button>
                      </div>
                    </article>
                  );
                })}
              </div>
            </>
          )}
        </section>
      </main>
    </>
  );
}

export default ProductsPage;
