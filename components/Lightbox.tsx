'use client'

import { useCallback, useEffect, useRef, useState } from "react"
import Image from "next/image"
import { motion } from "framer-motion"
import type { Artwork } from "@/lib/data"
import { partField } from "@/lib/fields"
import { requestArtworkInfo, buildInquiryMailto } from "@/lib/contactPrefill"
import bio from "@/data/bio.json"

interface LightboxProps {
  works: Artwork[]
  initialIndex: number
  onClose: () => void
}

const MIN_ZOOM = 1
const MAX_ZOOM = 3
const DOUBLE_TAP_ZOOM = 2.5
const ZOOM_STEP = 0.5
const WHEEL_STEP = 0.4
const DOUBLE_TAP_MS = 300
const TAP_SLOP_PX = 10

export default function Lightbox({ works, initialIndex, onClose }: LightboxProps) {
  const [currentIndex, setCurrentIndex] = useState(initialIndex)
  const [zoom, setZoom] = useState(MIN_ZOOM)
  const [offset, setOffset] = useState({ x: 0, y: 0 })
  // true durante un gesto attivo: la transizione di Framer Motion va a 0
  const [interacting, setInteracting] = useState(false)

  const dialogRef = useRef<HTMLDivElement>(null)

  // Swipe di navigazione (overlay, solo a zoom 1×)
  const swipeStartX = useRef(0)
  const didSwipe = useRef(false)

  // Pan / pinch / double-tap (contenitore immagine)
  const activePointers = useRef(new Map<number, { x: number; y: number }>())
  const pinchStartDistance = useRef(0)
  const pinchStartZoom = useRef(MIN_ZOOM)
  const panPointerStart = useRef({ x: 0, y: 0 })
  const panOffsetStart = useRef({ x: 0, y: 0 })
  const didPan = useRef(false)
  const lastTapTime = useRef(0)
  const downPosition = useRef({ x: 0, y: 0 })

  const work = works[currentIndex]
  const isZoomed = zoom > MIN_ZOOM

  // L'offset non può portare l'immagine oltre metà viewport scalato:
  // l'opera resta sempre almeno parzialmente visibile.
  const clampOffset = (x: number, y: number, z: number) => {
    const maxX = (window.innerWidth * (z - 1)) / 2
    const maxY = (window.innerHeight * (z - 1)) / 2
    return {
      x: Math.min(maxX, Math.max(-maxX, x)),
      y: Math.min(maxY, Math.max(-maxY, y)),
    }
  }

  const applyZoom = useCallback((next: number) => {
    const z = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, next))
    setZoom(z)
    setOffset((prev) => (z === MIN_ZOOM ? { x: 0, y: 0 } : clampOffset(prev.x, prev.y, z)))
  }, [])

  const resetView = useCallback(() => {
    setZoom(MIN_ZOOM)
    setOffset({ x: 0, y: 0 })
  }, [])

  const goToPrev = useCallback(() => {
    setCurrentIndex((i) => (i - 1 + works.length) % works.length)
    resetView()
  }, [works.length, resetView])

  const goToNext = useCallback(() => {
    setCurrentIndex((i) => (i + 1) % works.length)
    resetView()
  }, [works.length, resetView])

  const handleInquiry = () => {
    const target = document.getElementById("contact")
    if (!target) {
      // Nessuna sezione Contatti in pagina: fallback mailto
      window.location.href = buildInquiryMailto(bio.email, {
        title: work.title ?? work.alt,
        medium: work.medium,
        size: work.size,
      })
      return
    }
    requestArtworkInfo({ title: work.title ?? work.alt, medium: work.medium, size: work.size })
    // Sblocca subito lo scroll (l'effetto di cleanup arriverebbe solo a fine exit animation)
    document.body.style.overflow = ""
    onClose()
    requestAnimationFrame(() => target.scrollIntoView({ behavior: "smooth" }))
  }

  // Lock body scroll
  useEffect(() => {
    const prev = document.body.style.overflow
    document.body.style.overflow = "hidden"
    return () => { document.body.style.overflow = prev }
  }, [])

  // Restore focus on close
  useEffect(() => {
    const previousFocus = document.activeElement as HTMLElement | null
    const firstButton = dialogRef.current?.querySelector<HTMLElement>("button")
    firstButton?.focus()
    return () => { previousFocus?.focus() }
  }, [])

  // Keyboard: Escape/frecce/focus trap (come prima) + zoom con + − 0
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") { onClose(); return }
      if (e.key === "ArrowLeft") { goToPrev(); return }
      if (e.key === "ArrowRight") { goToNext(); return }
      if (e.key === "+" || e.key === "=") { applyZoom(zoom + ZOOM_STEP); return }
      if (e.key === "-" || e.key === "_") { applyZoom(zoom - ZOOM_STEP); return }
      if (e.key === "0") { resetView(); return }

      if (e.key === "Tab") {
        const focusable = dialogRef.current?.querySelectorAll<HTMLElement>("button")
        if (!focusable || focusable.length === 0) return
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (e.shiftKey) {
          if (document.activeElement === first) { e.preventDefault(); last.focus() }
        } else {
          if (document.activeElement === last) { e.preventDefault(); first.focus() }
        }
      }
    }
    window.addEventListener("keydown", handleKey)
    return () => window.removeEventListener("keydown", handleKey)
  }, [onClose, goToPrev, goToNext, applyZoom, resetView, zoom])

  // ── Overlay: swipe di navigazione (solo a zoom 1×) e chiusura ──
  const onOverlayPointerDown = (e: React.PointerEvent) => {
    swipeStartX.current = e.clientX
    didSwipe.current = false
  }
  const onOverlayPointerUp = (e: React.PointerEvent) => {
    if (isZoomed) return // da zoomati si naviga con frecce/tastiera, il drag è pan
    const delta = e.clientX - swipeStartX.current
    if (delta > 60) { goToPrev(); didSwipe.current = true }
    if (delta < -60) { goToNext(); didSwipe.current = true }
  }
  const handleOverlayClick = () => {
    if (!didSwipe.current) onClose()
  }

  // ── Contenitore immagine: pinch, pan, double-tap ──
  const pointDistance = (a: { x: number; y: number }, b: { x: number; y: number }) =>
    Math.hypot(a.x - b.x, a.y - b.y)

  const onImagePointerDown = (e: React.PointerEvent) => {
    e.currentTarget.setPointerCapture(e.pointerId)
    activePointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY })
    didPan.current = false
    downPosition.current = { x: e.clientX, y: e.clientY }
    setInteracting(true)

    const points = [...activePointers.current.values()]
    if (points.length === 2) {
      pinchStartDistance.current = pointDistance(points[0], points[1])
      pinchStartZoom.current = zoom
    } else if (points.length === 1 && isZoomed) {
      panPointerStart.current = { x: e.clientX, y: e.clientY }
      panOffsetStart.current = offset
    }
  }

  const onImagePointerMove = (e: React.PointerEvent) => {
    if (!activePointers.current.has(e.pointerId)) return
    activePointers.current.set(e.pointerId, { x: e.clientX, y: e.clientY })
    const points = [...activePointers.current.values()]

    if (points.length === 2 && pinchStartDistance.current > 0) {
      const ratio = pointDistance(points[0], points[1]) / pinchStartDistance.current
      applyZoom(pinchStartZoom.current * ratio)
      return
    }

    if (points.length === 1 && isZoomed) {
      const dx = e.clientX - panPointerStart.current.x
      const dy = e.clientY - panPointerStart.current.y
      if (Math.hypot(dx, dy) > TAP_SLOP_PX) didPan.current = true
      setOffset(clampOffset(panOffsetStart.current.x + dx, panOffsetStart.current.y + dy, zoom))
    }
  }

  const onImagePointerUp = (e: React.PointerEvent) => {
    activePointers.current.delete(e.pointerId)
    if (activePointers.current.size === 0) setInteracting(false)
    pinchStartDistance.current = 0

    // Double-tap (touch) / double-click (mouse): toggle zoom
    const moved = pointDistance(downPosition.current, { x: e.clientX, y: e.clientY })
    if (moved <= TAP_SLOP_PX && !didPan.current) {
      const now = Date.now()
      if (now - lastTapTime.current < DOUBLE_TAP_MS) {
        if (isZoomed) resetView()
        else applyZoom(DOUBLE_TAP_ZOOM)
        lastTapTime.current = 0
      } else {
        lastTapTime.current = now
      }
    }
  }

  const onImageWheel = (e: React.WheelEvent) => {
    applyZoom(zoom - Math.sign(e.deltaY) * WHEEL_STEP)
  }

  const title = work.title ?? work.alt
  const field = partField(work.field, currentIndex)

  // The overlay is a card on the still's own field. It cuts in: no fade.
  return (
    <div
      ref={dialogRef}
      role="dialog"
      aria-modal="true"
      aria-label={title}
      className={`screen-overlay f-${field}`}
      onClick={handleOverlayClick}
      onPointerDown={onOverlayPointerDown}
      onPointerUp={onOverlayPointerUp}
    >
      <span className="keyline" aria-hidden="true" />

      <div className="screen-controls" onClick={(e) => e.stopPropagation()}>
        <button type="button" className="text-button" onClick={goToPrev} aria-label="Previous still">
          Previous
        </button>
        <button type="button" className="text-button" onClick={() => applyZoom(zoom - ZOOM_STEP)} aria-label="Zoom out">
          −
        </button>
        <button type="button" className="text-button" onClick={() => applyZoom(zoom + ZOOM_STEP)} aria-label="Zoom in">
          +
        </button>
        {isZoomed && (
          <button type="button" className="text-button" onClick={resetView} aria-label="Reset zoom">
            100%
          </button>
        )}
        <button type="button" className="text-button" onClick={goToNext} aria-label="Next still">
          Next
        </button>
        <button type="button" className="text-button" onClick={onClose}>
          Close
        </button>
      </div>

      <div
        className="flex flex-col items-center max-w-[90vw]"
        onClick={(e) => e.stopPropagation()}
      >
        <motion.div
          className={`relative lightbox-image ${isZoomed ? "cursor-grab" : ""}`}
          style={{ touchAction: "none" }}
          animate={{ x: offset.x, y: offset.y, scale: zoom }}
          transition={interacting ? { duration: 0 } : { type: "tween", duration: 0.2 }}
          onPointerDown={onImagePointerDown}
          onPointerMove={onImagePointerMove}
          onPointerUp={onImagePointerUp}
          onPointerCancel={onImagePointerUp}
          onWheel={onImageWheel}
        >
          <Image
            src={work.blurDataURL ? `/assets-opt/${work.file}` : `/assets/${work.file}`}
            alt={work.alt}
            fill
            sizes={isZoomed ? "200vw" : "90vw"}
            className="object-contain"
            draggable={false}
          />
        </motion.div>
        {!isZoomed && (
          <div className="lightbox-caption">
            <p className="cell-title">{currentIndex + 1}. {title}</p>
            {work.note && <p className="cell-note">{work.note}</p>}
            {(work.medium || work.size) && (
              <p className="cell-note">{[work.medium, work.size].filter(Boolean).join(", ")}</p>
            )}
            {work.credit && <p className="cell-note">Still by {work.credit}</p>}
            {bio.email && (
              <button
                type="button"
                className="text-button mt-2"
                onClick={(e) => { e.stopPropagation(); handleInquiry() }}
              >
                Ask about this still
              </button>
            )}
          </div>
        )}
      </div>

      {/* Preload the previous and next still out of sight */}
      <div className="fixed inset-0 opacity-0 pointer-events-none -z-10" aria-hidden="true">
        {[-1, 1].map((offsetIdx) => {
          const idx = (currentIndex + offsetIdx + works.length) % works.length
          const w = works[idx]
          return (
            <div key={idx} className="relative w-full h-full">
              <Image
                src={w.blurDataURL ? `/assets-opt/${w.file}` : `/assets/${w.file}`}
                alt=""
                fill
                sizes="90vw"
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}
