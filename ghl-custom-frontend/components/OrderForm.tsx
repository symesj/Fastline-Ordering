import { ChangeEvent, FormEvent, useState } from "react";
import { createOrder } from "../lib/api";
import { CreateOrderPayload } from "../types/orders";

type OrderFormState = Omit<CreateOrderPayload, "total"> & { total: string };

const defaultForm: OrderFormState = {
  customerName: "",
  customerEmail: "",
  items: [],
  notes: "",
  total: ""
};

export function OrderForm(): JSX.Element {
  const [form, setForm] = useState<OrderFormState>(defaultForm);

  const updateField = <K extends keyof OrderFormState>(
    key: K,
    value: OrderFormState[K]
  ) => {
    setForm((previous: OrderFormState) => ({
      ...previous,
      [key]: value
    }));
  };

  const handleInputChange = <
    K extends "customerName" | "customerEmail" | "notes" | "total"
  >(
    key: K
  ) => (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    updateField(key, event.target.value as OrderFormState[K]);
  };

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const { total, ...rest } = form;
    const parsedTotal = total.trim() === "" ? 0 : Number.parseFloat(total);
    const safeTotal = Number.isFinite(parsedTotal) ? parsedTotal : 0;

    const payload: CreateOrderPayload = {
      ...(rest as Omit<CreateOrderPayload, "total">),
      total: safeTotal
    };

    await createOrder(payload);
    setForm(defaultForm);
  };

  return (
    <form onSubmit={onSubmit}>
      <div>
        <label htmlFor="customerName">Customer Name</label>
        <input
          id="customerName"
          name="customerName"
          value={form.customerName}
          onChange={handleInputChange("customerName")}
        />
      </div>

      <div>
        <label htmlFor="customerEmail">Customer Email</label>
        <input
          id="customerEmail"
          name="customerEmail"
          value={form.customerEmail}
          onChange={handleInputChange("customerEmail")}
        />
      </div>

      <div>
        <label htmlFor="total">Order Total</label>
        <input
          id="total"
          name="total"
          value={form.total}
          onChange={handleInputChange("total")}
        />
      </div>

      <div>
        <label htmlFor="notes">Notes</label>
        <textarea
          id="notes"
          name="notes"
          value={form.notes ?? ""}
          onChange={handleInputChange("notes")}
        />
      </div>

      <button type="submit">Create Order</button>
    </form>
  );
}
