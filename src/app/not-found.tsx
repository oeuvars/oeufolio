import Link from "next/link";
import { IconArrowLeft, IconArrowUpRight } from "@tabler/icons-react";
import { AmbientField } from "@/components/ambient-field";

export default function NotFound() {
  return (
    <main className="error-shell">
      <AmbientField signal={1} engaged={false} />
      <div className="error-chassis" aria-hidden="true" />

      <header className="error-header">
        <div className="error-identity">
          <i aria-hidden="true" />
          <div>
            <span>Anurag Das</span>
            <small>Personal receiver / AD–404</small>
          </div>
        </div>
        <span>Frequency unavailable</span>
      </header>

      <section className="error-stage" aria-labelledby="error-title">
        <div className="error-number" aria-hidden="true">404</div>

        <div className="error-screen">
          <div className="error-static" aria-hidden="true" />
          <span className="frame-cross frame-cross-a" aria-hidden="true" />
          <span className="frame-cross frame-cross-b" aria-hidden="true" />

          <span className="error-register">error / 404</span>
          <div className="error-copy">
            <span>No signal</span>
            <h1 id="error-title">Nothing here.</h1>
            <p>This frequency does not exist.</p>
          </div>

          <Link href="/" className="error-home-link">
            <IconArrowLeft size={14} stroke={1.5} /> Return to 88.4
          </Link>
        </div>

        <aside className="error-readout" aria-label="Error information">
          <div>
            <span>band</span>
            <strong>— — —</strong>
          </div>
          <div>
            <span>source</span>
            <strong>not found</strong>
          </div>
          <div>
            <span>status</span>
            <strong>off air</strong>
          </div>
        </aside>
      </section>

      <footer className="error-deck">
        <div>
          <span>field selector</span>
          <strong>404.0</strong>
          <small>MHz</small>
        </div>

        <div className="error-tuner" aria-hidden="true">
          <span>88</span>
          <i />
          <span>106</span>
        </div>

        <Link href="/">
          Receiver <IconArrowUpRight size={13} stroke={1.5} />
        </Link>
      </footer>
    </main>
  );
}
