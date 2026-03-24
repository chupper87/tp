import { useActiveMeasures } from "../hooks";
import type {
  ScheduleCustomerOut,
  ScheduleMeasureOut,
  CustomerFulfillment,
  MeasureBrief,
} from "../types";
import FulfillmentCard from "./FulfillmentCard";

interface MeasuresSectionProps {
  scheduleId: string;
  customers: ScheduleCustomerOut[];
  measures: ScheduleMeasureOut[];
  fulfillmentCustomers: CustomerFulfillment[];
}

export default function MeasuresSection({
  scheduleId,
  customers,
  measures,
  fulfillmentCustomers,
}: MeasuresSectionProps) {
  const { data: allMeasures } = useActiveMeasures();

  // Build measure lookup
  const measureMap = new Map<string, MeasureBrief>();
  for (const m of allMeasures ?? []) {
    measureMap.set(m.id, m);
  }

  // Index fulfillment data by customer_id
  const fulfillmentByCustomer = new Map<string, CustomerFulfillment>();
  for (const cf of fulfillmentCustomers) {
    fulfillmentByCustomer.set(cf.customer_id, cf);
  }

  if (customers.length === 0) {
    return (
      <div className="card-glow rounded-xl bg-ocean/60 p-4">
        <h3 className="text-sm font-600 text-moon mb-3">Planerade insatser</h3>
        <p className="text-xs text-sediment">
          Tilldela kunder till schemat för att planera insatser
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {customers.map((sc) => {
        const fulfillment = fulfillmentByCustomer.get(sc.customer_id);

        // If no fulfillment data (no care plan), create a minimal one
        const customerFulfillment: CustomerFulfillment = fulfillment ?? {
          customer_id: sc.customer_id,
          customer_name: `${sc.customer.first_name} ${sc.customer.last_name}`,
          care_level: null,
          required_measures: [],
          total_required: 0,
          total_fulfilled: 0,
          total_duration_minutes: 0,
        };

        return (
          <FulfillmentCard
            key={sc.customer_id}
            scheduleId={scheduleId}
            customer={customerFulfillment}
            scheduleMeasures={measures}
            measureMap={measureMap}
          />
        );
      })}
    </div>
  );
}
