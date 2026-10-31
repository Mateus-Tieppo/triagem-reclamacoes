"use client";

import gsap from "gsap";
import { useGSAP } from "@gsap/react";
import type { RefObject } from "react";

gsap.registerPlugin(useGSAP);

/** As barras crescem uma vez ao abrir o painel. Quem pede menos movimento vê tudo pronto. */
export function useCrescer(escopo: RefObject<HTMLElement | null>, seletor: string, eixo: "x" | "y") {
  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      mm.add("(prefers-reduced-motion: no-preference)", () => {
        gsap.from(seletor, {
          ...(eixo === "x" ? { scaleX: 0, transformOrigin: "left center" } : { scaleY: 0, transformOrigin: "center bottom" }),
          duration: 0.7,
          ease: "power3.out",
          stagger: 0.04,
        });
      });
      return () => mm.revert();
    },
    { scope: escopo },
  );
}
