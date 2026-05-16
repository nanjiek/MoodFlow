import { useContext } from "react";

import { ToastContext } from "@/providers/toast-provider";

export function useToast() {
  return useContext(ToastContext);
}
