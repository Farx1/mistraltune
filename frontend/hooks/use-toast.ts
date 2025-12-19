"use client"

import * as React from "react"
import { toast as sonnerToast } from "sonner"

export interface ToastProps {
  title?: string
  description?: string
  variant?: "default" | "destructive"
}

export function useToast() {
  const toast = ({ title, description, variant }: ToastProps) => {
    if (variant === "destructive") {
      sonnerToast.error(title || "Erreur", {
        description,
      })
    } else {
      sonnerToast.success(title || "Succès", {
        description,
      })
    }
  }

  return { toast }
}

