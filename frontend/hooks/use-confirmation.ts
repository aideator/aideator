"use client"

import { useState, useCallback } from 'react'

interface ConfirmationOptions {
  title: string
  description: string
  confirmText?: string
  cancelText?: string
  variant?: 'default' | 'destructive'
}

interface ConfirmationState extends ConfirmationOptions {
  isOpen: boolean
  isLoading: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function useConfirmation() {
  const [state, setState] = useState<ConfirmationState>({
    isOpen: false,
    isLoading: false,
    title: '',
    description: '',
    confirmText: 'Confirm',
    cancelText: 'Cancel',
    variant: 'default',
    onConfirm: () => {},
    onCancel: () => {},
  })

  const confirm = useCallback((
    options: ConfirmationOptions,
    onConfirm: () => Promise<void> | void
  ): Promise<boolean> => {
    return new Promise((resolve) => {
      setState({
        ...options,
        isOpen: true,
        isLoading: false,
        confirmText: options.confirmText || 'Confirm',
        cancelText: options.cancelText || 'Cancel',
        variant: options.variant || 'default',
        onConfirm: async () => {
          try {
            setState(prev => ({ ...prev, isLoading: true }))
            await onConfirm()
            setState(prev => ({ ...prev, isOpen: false, isLoading: false }))
            resolve(true)
          } catch (error) {
            setState(prev => ({ ...prev, isLoading: false }))
            // Let the error bubble up to the caller
            throw error
          }
        },
        onCancel: () => {
          setState(prev => ({ ...prev, isOpen: false, isLoading: false }))
          resolve(false)
        },
      })
    })
  }, [])

  const close = useCallback(() => {
    setState(prev => ({ ...prev, isOpen: false, isLoading: false }))
  }, [])

  return {
    ...state,
    confirm,
    close,
  }
}