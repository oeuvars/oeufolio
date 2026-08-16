"use client";

import Image from "next/image";
import Link from "next/link";
import { IconArrowUpRight } from "@tabler/icons-react";
import {
  type CSSProperties,
  type KeyboardEvent,
  type PointerEvent,
  type WheelEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import { AmbientField } from "@/components/ambient-field";

const signals = [
  {
    number: "01",
    frequency: "88.4",
    title: "after six",
    note: "One more take. Then another.",
    register: "E♭ / AMP WARM",
    time: "18:42",
    location: "ROOM / WEST WALL",
    src: "/images/journal/guitar.jpg",
    alt: "A cream electric guitar resting on a deep green rug beside a coiled cable and red pick",
    position: "43% 55%",
    color: "#a45249",
  },
  {
    number: "02",
    frequency: "91.7",
    title: "within reach",
    note: "Good buttons do not need instructions.",
    register: "A–07 / DESK LAMP ON",
    time: "22:16",
    location: "DESK / LEFT SIDE",
    src: "/images/journal/electronics.jpg",
    alt: "A compact aluminum music device with tactile colored controls, headphones, and a notebook",
    position: "50% 52%",
    color: "#5575a5",
  },
  {
    number: "03",
    frequency: "96.3",
    title: "the longer way",
    note: "Parked. Looked back.",
    register: "06:10 / NO DIRECT ROUTE",
    time: "06:10",
    location: "EAST / BEFORE TRAFFIC",
    src: "/images/journal/sports-car.jpg",
    alt: "A silver sports coupe parked beneath a concrete structure at dawn",
    position: "50% 53%",
    color: "#5d7767",
  },
  {
    number: "04",
    frequency: "101.1",
    title: "desk occupied",
    note: "I was using that.",
    register: "15:42 / UNSAVED",
    time: "15:42",
    location: "DESK / EXACT CENTRE",
    src: "/images/journal/cat.jpg",
    alt: "A tuxedo cat sitting on an open notebook beside a compact keyboard and pencil",
    position: "57% 51%",
    color: "#a88742",
  },
  {
    number: "05",
    frequency: "105.8",
    title: "ninety minutes",
    note: "Everything else moved.",
    register: "N5 / MATCH DAY",
    time: "MATCH DAY",
    location: "HOME / NORTH LONDON",
    src: "/images/journal/arsenal.jpg",
    alt: "A red and white scarf, leather football, notebook, and ticket on concrete stadium steps",
    position: "50% 55%",
    color: "#b24d43",
  },
] as const;

type ReceiverStyle = CSSProperties & {
  "--signal-color": string;
  "--lens-x": string;
  "--lens-y": string;
  "--station": string;
  "--dial-turn": string;
};

const wrapSignal = (index: number) =>
  (index + signals.length) % signals.length;

export function LifeReceiver() {
  const [activeIndex, setActiveIndex] = useState(0);
  const [engaged, setEngaged] = useState(false);
  const [clock, setClock] = useState("--:--");
  const [lens, setLens] = useState({ x: 52, y: 48 });
  const wheelLock = useRef(0);
  const touchStart = useRef<number | null>(null);
  const signal = signals[activeIndex];

  const tuneTo = useCallback((index: number) => {
    setActiveIndex(wrapSignal(index));
    setEngaged(true);
  }, []);

  useEffect(() => {
    const updateClock = () => {
      setClock(
        new Intl.DateTimeFormat("en-GB", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
          timeZone: "Asia/Kolkata",
        }).format(new Date()),
      );
    };

    updateClock();
    const interval = window.setInterval(updateClock, 30_000);
    return () => window.clearInterval(interval);
  }, []);

  const handleWheel = (event: WheelEvent<HTMLElement>) => {
    if (Math.abs(event.deltaY) < 18 && Math.abs(event.deltaX) < 18) return;

    const now = window.performance.now();
    if (now < wheelLock.current) return;

    const direction = Math.abs(event.deltaY) >= Math.abs(event.deltaX)
      ? Math.sign(event.deltaY)
      : Math.sign(event.deltaX);

    wheelLock.current = now + 460;
    tuneTo(activeIndex + direction);
  };

  const handleKeys = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault();
      tuneTo(activeIndex + 1);
    }

    if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault();
      tuneTo(activeIndex - 1);
    }
  };

  const handleLens = (event: PointerEvent<HTMLDivElement>) => {
    const bounds = event.currentTarget.getBoundingClientRect();
    setLens({
      x: ((event.clientX - bounds.left) / bounds.width) * 100,
      y: ((event.clientY - bounds.top) / bounds.height) * 100,
    });
    setEngaged(true);
  };

  const handleTouchStart = (event: PointerEvent<HTMLElement>) => {
    if (event.pointerType === "touch") touchStart.current = event.clientX;
  };

  const handleTouchEnd = (event: PointerEvent<HTMLElement>) => {
    if (event.pointerType !== "touch" || touchStart.current === null) return;
    const distance = event.clientX - touchStart.current;
    touchStart.current = null;

    if (Math.abs(distance) > 42) {
      tuneTo(activeIndex + (distance < 0 ? 1 : -1));
    }
  };

  const receiverStyle: ReceiverStyle = {
    "--signal-color": signal.color,
    "--lens-x": `${lens.x}%`,
    "--lens-y": `${lens.y}%`,
    "--station": `${(activeIndex / (signals.length - 1)) * 100}%`,
    "--dial-turn": `${-58 + activeIndex * 29}deg`,
  };

  return (
    <main
      className="receiver"
      data-engaged={engaged}
      data-signal={signal.number}
      style={receiverStyle}
      onWheel={handleWheel}
      onKeyDown={handleKeys}
      onPointerDown={handleTouchStart}
      onPointerUp={handleTouchEnd}
    >
      <AmbientField signal={activeIndex} engaged={engaged} />
      <div className="receiver-chassis" aria-hidden="true" />

      <header className="receiver-header">
        <div className="receiver-identity">
          <i aria-hidden="true" />
          <div>
            <h1>Anurag Das</h1>
            <span>Personal receiver / AD–01</span>
          </div>
        </div>

        <div className="receiver-clock">
          <time>{clock}</time>
          <span>Kolkata / IST</span>
        </div>

        <Link className="receiver-elsewhere" href="/contact">
          Elsewhere <IconArrowUpRight size={13} stroke={1.5} />
        </Link>
      </header>

      <section
        className="receiver-stage"
        aria-label={`Signal ${signal.number}: ${signal.title}`}
        tabIndex={0}
      >
        <div className="signal-index" aria-hidden="true">
          <span>signal</span>
          <strong>{signal.number}</strong>
          <small>of {signals.length.toString().padStart(2, "0")}</small>
        </div>

        <div className="signal-copy" key={`copy-${signal.number}`}>
          <span className="signal-kicker">currently receiving</span>
          <h2>{signal.title}</h2>
          <p>{signal.note}</p>
          <div className="signal-register">
            <span>{signal.register}</span>
            <i />
          </div>
        </div>

        <figure className="signal-figure">
          <div
            className="signal-picture"
            onPointerMove={handleLens}
            onPointerEnter={() => setEngaged(true)}
          >
            <Image
              key={`base-${signal.number}`}
              className="signal-image signal-image-base"
              src={signal.src}
              alt={signal.alt}
              fill
              loading="eager"
              sizes="(max-width: 760px) 100vw, 60vw"
              style={{ objectPosition: signal.position }}
            />
            <Image
              key={`colour-${signal.number}`}
              className="signal-image signal-image-colour"
              src={signal.src}
              alt=""
              fill
              aria-hidden="true"
              loading="eager"
              sizes="(max-width: 760px) 100vw, 60vw"
              style={{ objectPosition: signal.position }}
            />
            <div className="signal-scan" aria-hidden="true" />
            <div className="image-register" aria-hidden="true">
              <span className="image-register-mark">
                <i />
                <b>rx/{signal.number}</b>
              </span>
              <span className="image-register-track">
                {signals.map((item, index) => (
                  <i
                    key={item.number}
                    data-active={index === activeIndex}
                  />
                ))}
              </span>
              <small>{engaged ? "open" : "idle"}</small>
            </div>
            <p className="receiver-prompt">Move over the picture / tune below</p>
          </div>

          <span className="frame-cross frame-cross-a" aria-hidden="true" />
          <span className="frame-cross frame-cross-b" aria-hidden="true" />

          <figcaption>
            <span>{signal.number} / {signal.time}</span>
            <span>{signal.location}</span>
          </figcaption>
        </figure>

        <aside className="receiver-readout" aria-label="Receiver information">
          <div className="attention-meter">
            <span>attention</span>
            <div><i /></div>
            <output>{engaged ? "open" : "idle"}</output>
          </div>

          <dl>
            <div>
              <dt>band</dt>
              <dd>{signal.frequency} MHz</dd>
            </div>
            <div>
              <dt>source</dt>
              <dd>personal / {signal.number}</dd>
            </div>
            <div>
              <dt>status</dt>
              <dd>kept nearby</dd>
            </div>
          </dl>

          <div className="receiver-monitor" aria-hidden="true">
            <div className="monitor-grille" />
            <div className="monitor-label">
              <span>monitor</span>
              <i />
              <small>{signal.number} / rx</small>
            </div>
          </div>

          <div className="open-circuit">
            <span>open circuit / 02</span>
            <Link href="https://github.com/oeuvars" target="_blank" rel="noreferrer">
              GitHub <IconArrowUpRight size={11} stroke={1.5} />
            </Link>
            <Link href="https://cybership.io" target="_blank" rel="noreferrer">
              Cybership <IconArrowUpRight size={11} stroke={1.5} />
            </Link>
          </div>
        </aside>
      </section>

      <section className="tuning-deck" aria-label="Personal signal selector">
        <div className="deck-label">
          <span>field selector</span>
          <strong>{signal.frequency}</strong>
          <small>MHz</small>
        </div>

        <div className="tuner-assembly">
          <div className="tuner-meta">
            <span>88</span>
            <output>{signal.number} / {signals.length.toString().padStart(2, "0")}</output>
            <span>106</span>
          </div>

          <div className="tuner-track">
            <div className="tuner-ticks" aria-hidden="true" />
            <i className="tuner-needle" aria-hidden="true" />
            {signals.map((item, index) => (
              <button
                key={item.number}
                className="tuner-station"
                data-active={index === activeIndex}
                style={{ left: `${(index / (signals.length - 1)) * 100}%` }}
                type="button"
                aria-label={`Tune to signal ${item.number}`}
                aria-pressed={index === activeIndex}
                onClick={() => tuneTo(index)}
              >
                <span>{item.number}</span>
              </button>
            ))}
            <input
              type="range"
              min="0"
              max={signals.length - 1}
              step="1"
              value={activeIndex}
              aria-label="Tune between personal signals"
              onChange={(event) => tuneTo(Number(event.currentTarget.value))}
            />
          </div>

          <p>scroll / drag / arrow keys</p>
        </div>

        <div className="control-bank">
          <div className="control-keys">
            <button
              type="button"
              aria-label="Previous signal"
              onClick={() => tuneTo(activeIndex - 1)}
            >
              <span>−</span><small>prev</small>
            </button>
            <button
              type="button"
              aria-label="Next signal"
              onClick={() => tuneTo(activeIndex + 1)}
            >
              <span>+</span><small>next</small>
            </button>
            <button
              type="button"
              aria-label="Open signal colour"
              onClick={() => setEngaged(true)}
            >
              <span>●</span><small>open</small>
            </button>
            <button
              type="button"
              aria-label="Return signal to idle"
              onClick={() => setEngaged(false)}
            >
              <span>○</span><small>idle</small>
            </button>
          </div>
          <button
            type="button"
            className="control-dial"
            aria-label="Tune to next signal"
            onClick={() => tuneTo(activeIndex + 1)}
          >
            <span />
            <small>select</small>
          </button>
        </div>
      </section>
    </main>
  );
}
