import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import ChatWidget from "@/components/ChatWidget";

export const metadata: Metadata = {
  title: "Zentra – Modern E-Commerce",
  description: "Zentra – AI-powered smart shopping assistant",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main style={{ maxWidth: "1280px", margin: "0 auto", padding: "2rem 1.5rem" }}>
          {children}
        </main>
        <ChatWidget />
      </body>
    </html>
  );
}
