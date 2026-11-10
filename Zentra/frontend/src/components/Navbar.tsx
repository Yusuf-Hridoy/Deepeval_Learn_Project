"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { fetchCart } from "@/lib/api";

export default function Navbar() {
  const [cartCount, setCartCount] = useState(0);
  const pathname = usePathname();

  useEffect(() => {
    const load = async () => {
      try {
        const cart = await fetchCart();
        setCartCount(cart.items.reduce((s, i) => s + i.quantity, 0));
      } catch {}
    };
    load();
    const id = setInterval(load, 4000);
    window.addEventListener("cart-updated", load);
    return () => {
      clearInterval(id);
      window.removeEventListener("cart-updated", load);
    };
  }, []);

  const navLink = (href: string, label: string) => {
    const active = pathname === href;
    return (
      <Link href={href} style={{
        color: active ? "#ffffff" : "rgba(255,255,255,0.7)",
        fontWeight: active ? 600 : 400,
        fontSize: "0.9rem",
        padding: "0.4rem 0.75rem",
        borderRadius: "8px",
        background: active ? "rgba(255,255,255,0.15)" : "transparent",
        transition: "all 150ms",
      }}>
        {label}
      </Link>
    );
  };

  return (
    <nav style={{
      background: "linear-gradient(135deg, #042f2e 0%, #0f3d3a 50%, #115e59 100%)",
      borderBottom: "1px solid rgba(255,255,255,0.08)",
      padding: "0 2rem",
      height: "64px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      position: "sticky",
      top: 0,
      zIndex: 100,
      boxShadow: "0 4px 20px rgba(0,0,0,0.25)",
    }}>
      {/* Logo */}
      <Link href="/" style={{
        display: "flex", alignItems: "center", gap: "0.6rem",
        color: "white", fontWeight: 800, fontSize: "1.2rem", letterSpacing: "-0.02em",
      }}>
        <span style={{
          background: "linear-gradient(135deg, #5eead4, #2dd4bf)",
          color: "#042f2e",
          borderRadius: "9px",
          width: "30px", height: "30px",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "1.05rem", fontWeight: 900, letterSpacing: "-0.04em",
        }}>Z</span>
        <span>Zentra<span style={{ color: "#5eead4", fontWeight: 500 }}>.</span></span>
      </Link>

      {/* Nav links */}
      <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
        {navLink("/", "Products")}
        {navLink("/orders", "Orders")}
      </div>

      {/* Cart */}
      <Link href="/cart" style={{
        display: "flex", alignItems: "center", gap: "0.5rem",
        background: "rgba(255,255,255,0.12)",
        border: "1px solid rgba(255,255,255,0.2)",
        color: "white", padding: "0.45rem 1rem",
        borderRadius: "10px", fontWeight: 500, fontSize: "0.9rem",
        backdropFilter: "blur(8px)",
        transition: "background 150ms",
      }}>
        🛒 Cart
        {cartCount > 0 && (
          <span style={{
            background: "#e07a3f",
            color: "#ffffff",
            borderRadius: "99px",
            minWidth: "22px", height: "22px",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "0.75rem", fontWeight: 700, padding: "0 5px",
          }}>{cartCount}</span>
        )}
      </Link>
    </nav>
  );
}
