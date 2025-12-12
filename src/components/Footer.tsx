import { Github, Mail, ExternalLink, Heart } from "lucide-react";

const footerLinks = [
  {
    title: "Resources",
    links: [
      { label: "NYC Open Data", href: "https://opendata.cityofnewyork.us/", external: true },
      { label: "City Council Calendar", href: "https://council.nyc.gov/calendar/", external: true },
      { label: "Community Boards", href: "https://www.nyc.gov/site/cau/community-boards/community-boards.page", external: true },
    ],
  },
  {
    title: "Project",
    links: [
      { label: "About", href: "#about", external: false },
      { label: "GitHub", href: "https://github.com", external: true },
      { label: "Contact Us", href: "mailto:hello@civicscout.nyc", external: false },
    ],
  },
];

export function Footer() {
  return (
    <footer 
      className="border-t border-border bg-secondary/30"
      role="contentinfo"
    >
      <div className="civic-container py-12">
        <div className="grid gap-8 md:grid-cols-3">
          {/* Brand Column */}
          <div>
            <div className="flex items-center gap-2 text-foreground">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                <span className="text-sm font-bold">NYC</span>
              </div>
              <span className="font-display text-lg font-bold">Civic Scout</span>
            </div>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-muted-foreground">
              Empowering New Yorkers to participate in local democracy by making 
              civic meetings accessible and understandable.
            </p>
            <div className="mt-6 flex gap-3">
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary text-muted-foreground transition-colors hover:bg-primary hover:text-primary-foreground focus-ring"
                aria-label="View project on GitHub"
              >
                <Github className="h-5 w-5" />
              </a>
              <a
                href="mailto:hello@civicscout.nyc"
                className="flex h-10 w-10 items-center justify-center rounded-lg bg-secondary text-muted-foreground transition-colors hover:bg-primary hover:text-primary-foreground focus-ring"
                aria-label="Contact us via email"
              >
                <Mail className="h-5 w-5" />
              </a>
            </div>
          </div>

          {/* Link Columns */}
          {footerLinks.map((section) => (
            <div key={section.title}>
              <h3 className="font-display text-sm font-semibold text-foreground">
                {section.title}
              </h3>
              <ul className="mt-4 space-y-3">
                {section.links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      target={link.external ? "_blank" : undefined}
                      rel={link.external ? "noopener noreferrer" : undefined}
                      className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground focus-ring rounded"
                    >
                      {link.label}
                      {link.external && (
                        <ExternalLink className="h-3 w-3" aria-hidden="true" />
                      )}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border pt-8 sm:flex-row">
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} NYC Civic Scout. Open source project.
          </p>
          <p className="flex items-center gap-1 text-sm text-muted-foreground">
            Made with <Heart className="h-4 w-4 text-accent" aria-label="love" /> for NYC
          </p>
        </div>

        {/* Data Attribution */}
        <div className="mt-6 rounded-lg bg-secondary/50 p-4 text-center">
          <p className="text-xs text-muted-foreground">
            Data sourced from{" "}
            <a 
              href="https://opendata.cityofnewyork.us/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="font-medium text-primary underline underline-offset-2 hover:no-underline"
            >
              NYC Open Data
            </a>
            . This is an independent civic technology project and is not affiliated with 
            the City of New York.
          </p>
        </div>
      </div>
    </footer>
  );
}
