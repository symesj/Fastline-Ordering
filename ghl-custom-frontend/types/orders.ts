export interface OrderItem {
  id: string;
  description: string;
  quantity: number;
  unitPrice: number;
}

export interface CreateOrderPayload {
  customerName: string;
  customerEmail: string;
  items: OrderItem[];
  notes?: string;
  total: number;
}
