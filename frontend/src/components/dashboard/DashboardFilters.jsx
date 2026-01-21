import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const DashboardFilters = ({
  countries,
  outlets,
  country,
  outlet,
  setCountry,
  setOutlet,
  onReset,
}) => {
  return (
    <div className="flex items-center gap-3 flex-wrap">
      <div className="min-w-[180px]">
        <Select value={country} onValueChange={setCountry}>
          <SelectTrigger>
            <SelectValue placeholder="Country" />
          </SelectTrigger>
          <SelectContent>
            {countries.map((c) => (
              <SelectItem key={c} value={c}>
                {c}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="min-w-[220px]">
        <Select value={outlet} onValueChange={setOutlet}>
          <SelectTrigger>
            <SelectValue placeholder="Outlet" />
          </SelectTrigger>
          <SelectContent>
            {outlets.map((o) => (
              <SelectItem key={o} value={o}>
                {o}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Button variant="secondary" onClick={onReset}>
        Reset
      </Button>
    </div>
  );
};

export default DashboardFilters;
