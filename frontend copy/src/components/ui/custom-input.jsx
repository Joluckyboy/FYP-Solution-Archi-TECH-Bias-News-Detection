import * as React from "react";
import { cn } from "@/lib/utils";
import { Search } from "lucide-react";

const CustomInput = React.forwardRef(({ className, type, ...props }, ref) => {
    return (
        <div className="relative flex items-center w-full">
            <span className="absolute left-3 text-gray-500">
                <Search />
            </span>
            <input
                type={type}
                className={cn(
                    "flex h-10 w-full rounded-3xl border-2 border-indigo-500 pl-10 pr-3 py-2 text-base file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
                    className
                )}
                ref={ref}
                {...props}
            />
        </div>
    );
});
CustomInput.displayName = "CustomInput";

export { CustomInput };