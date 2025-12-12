import { useState } from "react";
import { Menu, X, MapPin, User } from "lucide-react";
import { Button } from "@/components/ui/button";

const navLinks = [
  { label: "Home", href: "#home" },
  { label: "Map View", href: "#map" },
  { label: "About", href: "#about" },
];

export function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header 
      className="sticky top-0 z-50 w-full border-b border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80"
      role="banner"
    >
      <nav 
        className="civic-container flex h-16 items-center justify-between"
        aria-label="Main navigation"
      >
        {/* Logo */}
        <a 
          href="#home" 
          className="flex items-center gap-2 text-foreground transition-colors hover:text-primary"
          aria-label="NYC Civic Scout - Home"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <MapPin className="h-5 w-5" aria-hidden="true" />
          </div>
          <span className="font-display text-lg font-bold tracking-tight">
            NYC Civic Scout
          </span>
        </a>

        {/* Desktop Navigation */}
        <div className="hidden items-center gap-1 md:flex">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground focus-ring"
            >
              {link.label}
            </a>
          ))}
        </div>

        {/* Desktop CTA */}
        <div className="hidden items-center gap-3 md:flex">
          <Button variant="ghost" size="sm">
            <User className="mr-1.5 h-4 w-4" aria-hidden="true" />
            Login
          </Button>
          <Button variant="hero" size="sm">
            Subscribe
          </Button>
        </div>

        {/* Mobile Menu Button */}
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-expanded={mobileMenuOpen}
          aria-controls="mobile-menu"
          aria-label={mobileMenuOpen ? "Close menu" : "Open menu"}
        >
          {mobileMenuOpen ? (
            <X className="h-5 w-5" aria-hidden="true" />
          ) : (
            <Menu className="h-5 w-5" aria-hidden="true" />
          )}
        </Button>
      </nav>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div 
          id="mobile-menu"
          className="border-t border-border bg-card md:hidden"
          role="navigation"
          aria-label="Mobile navigation"
        >
          <div className="civic-container space-y-1 py-4">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                className="block rounded-lg px-4 py-3 text-sm font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </a>
            ))}
            <div className="flex gap-3 pt-4">
              <Button variant="outline" className="flex-1">
                Login
              </Button>
              <Button variant="hero" className="flex-1">
                Subscribe
              </Button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
