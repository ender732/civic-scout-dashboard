import { AlertCircle } from "lucide-react";
import { useEffect } from "react";
import { useToast } from "@/components/ui/use-toast";

export function MapPlaceholder() {
  const { toast } = useToast();

  useEffect(() => {
    // Inform the user once that the map is unavailable and needs API keys
    toast({
      title: "Map unavailable",
      description: "Configure API keys in .env to enable map visualization",
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div 
      className="relative h-full min-h-[400px] overflow-hidden rounded-xl border border-destructive/50 bg-destructive/5 flex items-center justify-center"
      role="alert"
      aria-label="Map requires API configuration"
    >
      <div className="text-center px-6 py-8 max-w-md">
        <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-foreground mb-2">
          Map Unavailable
        </h3>
        <p className="text-sm text-muted-foreground">
          Configure API keys in <code className="bg-muted px-1.5 py-0.5 rounded text-xs">.env</code> to enable map visualization
        </p>
      </div>
    </div>
  );
}
