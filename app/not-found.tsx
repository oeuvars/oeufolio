import Link from "next/link"
import Nav from "@/components/Nav"
import Footer from "@/components/Footer"

export default function NotFound() {
  return (
    <>
      <Nav field="red" />
      <main>
        <section className="card f-red" data-field="red">
          <div className="stage">
            <p className="label">Missing reel</p>
            <h1 className="title">Nothing here</h1>
            <Link href="/" className="text-button mt-8">Back to the opening</Link>
          </div>
        </section>
      </main>
      <Footer field="red" />
    </>
  )
}
