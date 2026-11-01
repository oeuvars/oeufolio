import type { Cv, PageId, PageMeta, Profile, ResumeLetter, Site } from './types'

export const profile: Profile = {
  handle: 'oeuvars',
  nav: [
    { to: '/', label: 'Basics' },
    { to: '/letter', label: 'Likes' },
    { to: '/work', label: 'Work' },
    { to: '/desk', label: 'Extras' },
    { to: '/contact', label: 'Contact' },
  ],
  badge: {
    src: '/objects/badge.avif',
    backdrop: { color: '#e3d3c1' },
    alt: 'An ID card in a clear vinyl holder on a steel ring. It reads The Performer, Drop 25, product-first engineer, Cybership. Name: Anurag Das. Occupation: Engineer. Shade: T3 Warm. The holder of this card is an official performer for me. 02-03X.',
  },
  letter: {
    src: '/objects/letter.avif',
    alt: "A handwritten letter, dated Oct 2026, too late. Hello younger me, I know what you're like, so I know you'll call all of this stupid. I'm telling you anyway. You pick up an electric guitar and you don't put it down. You learn to shave slowly, the old way, and it ends up being the part of the morning that is yours. You give your heart to Arsenal, which is a stupid thing to do with a heart. And the cats. You think you are not a cat person. Then Dilly falls asleep on top of your keyboard and it's wraps. It isn't impressive, any of it, and I wouldn't trade it. Take your time getting here. Cheers, Anurag. Drawn between the lines: an amplifier and a PRS Silver Sky, noted loud, preferably. A lathered face in a mirror saying stretch and go with the grain, beside a shelf holding a Merkur razor, a tub of Proraso and a bottle of Clubman, while a younger onlooker says how relaxing! Someone holding a scarf up at a football match on television, shouting Özil, and the onlooker saying golly! Dilly, white with a ginger cap and tail, asleep on a MacBook's keyboard after typing a line of k's. And me on a bench, pressing 225 lbs: damn, light work.",
  },
  resume: {
    href: '/resume.pdf',
    src: '/objects/resume.avif',
    alt: 'Résumé',
  },
  experience: [
    { period: 'Mar 2025 to now', org: 'Cybership' },
    { period: 'Jul 2024 to Mar 2025', org: 'Ekarth Ventures' },
    { period: 'Aug 2023 to Jul 2024', org: 'ProperSKU' },
  ],
  extras: {
    name: 'Anurag Das',
    career: 'Software Engineer building servers and interfaces at',
    company: { label: 'Cybership', href: 'https://cybership.io' },
    particulars: [
      { label: 'Name', value: 'Anurag Das' },
      { label: 'Goes by', value: 'Oeuvars' },
      { label: 'Based in', value: 'Kolkata, India' },
      { label: 'Picky about', value: 'Fonts' },
    ],
    likes: {
      record: { subject: 'Electric guitars', title: 'after six', note: 'One more take. Then another.' },
      recorder: { subject: 'Industrial design', title: 'within reach', note: 'Good buttons do not need instructions.' },
      key: { subject: 'Sports cars', title: 'the longer way', note: 'Parked. Looked back.' },
      ticket: { subject: 'Arsenal', title: 'ninety minutes', note: 'Everything else moved.' },
    },
    playlist: { title: 'Two x 3', href: 'https://open.spotify.com/playlist/6aMM3pxZ1qYxR3uiwtRBox' },
  },
  socials: [
    { label: 'GitHub', href: 'https://github.com/oeuvars' },
    { label: 'X', href: 'https://x.com/oeuvars' },
    { label: 'Instagram', href: 'https://instagram.com/oeuvars' },
  ],
  email: 'sudo@anurag.gg',
}

export const site: Site = {
  url: 'https://www.anurag.gg',
  name: 'Anurag Das',
  x: '@oeuvars',
  locale: 'en_US',
}

export const pages: Record<PageId, PageMeta> = {
  basics: {
    path: '/',
    title: 'Anurag Das, product engineer',
    description: "I'm Anurag Das, a product engineer in Kolkata. At Cybership I build the servers and the interfaces behind a 3PL fulfillment platform.",
    preview: { src: '/og/basics.jpg', alt: 'The site as a stack of file folders, open on an ID badge for Anurag Das.' },
  },
  letter: {
    path: '/letter',
    title: 'Likes | Anurag Das',
    description: 'A letter to my younger self about what I ended up loving: an electric guitar, shaving the slow way, Arsenal, and a cat called Dilly.',
    preview: { src: '/og/letter.jpg', alt: 'A handwritten letter to my younger self, with drawings between the lines.' },
  },
  work: {
    path: '/work',
    title: 'Work | Anurag Das',
    description: "Where I've worked, made into a film poster: Cybership since March 2025, and Ekarth Ventures and ProperSKU before that.",
    preview: { src: '/og/work.jpg', alt: 'A film poster called Human Experience, laid over the lit windows of an apartment block at night.' },
  },
  desk: {
    path: '/desk',
    title: 'Extras | Anurag Das',
    description: 'My desk and what I keep on it: my playlist Two x 3 on a record, a tape recorder, car keys, an Arsenal ticket, and a razor with its Proraso.',
    preview: { src: '/og/desk.jpg', alt: 'A green cutting mat under a lamp, with a record, a tape recorder, keys, an Arsenal ticket and a razor on it.' },
  },
  contact: {
    path: '/contact',
    title: 'Contact | Anurag Das',
    description: "A ticket with my email on it. Click the address to copy it. I'm oeuvars on GitHub, X and Instagram.",
    preview: { src: '/og/contact.jpg', alt: 'A ticket printed with the Howrah Bridge and my email address, lying on red leather beside a camera and stamps.' },
  },
  resume: {
    path: '/resume',
    title: 'Résumé | Anurag Das',
    description: 'My résumé, typed as a letter: Cybership since March 2025, and Nahar OM, ProperSKU and DataVerse India before that.',
    preview: { src: '/og/resume.jpg', alt: 'The top of my résumé, with Anurag Das set wide across it.' },
  },
}

export const cv: Cv = {
  name: 'Anurag Das',
  headline: 'Product engineer at Cybership',
  roles: [
    {
      company: 'Cybership.io',
      about: 'A 3PL fulfillment platform',
      href: 'https://cybership.io',
      place: 'Remote',
      title: 'Full Stack Developer',
      period: 'March 2025 to now',
      points: [
        'Single-handedly architected and implemented the complete Automation Rules engine from scratch (similar to Shopify Flow), enabling merchants to create complex conditional workflows with 50 trigger types, 16 condition operators with conditional and array operations, and 7 action types. Built a type-safe rule evaluation system using Zod validation that processes 50,000+ rule executions daily across order processing, inventory allocation and shipping automation.',
        'Built Cybership Desktop, a packing-station app that replaces the third-party PrintNode agent. It prints through the OS spooler, raw TCP, USB and HID, reads scales over serial, HID, USB, Bluetooth and TCP with 64 protocol decoders, and ships as signed, auto-updating macOS and Windows builds. Printing is idempotent across server and device through UUID keys, PostgreSQL row-lock claims, an audited job state machine and an fsynced on-device ledger that will not reprint a job interrupted by a crash.',
        'Owned production incidents that blocked customer warehouses from shipping, taking each from first report through root cause to a permanent fix, often the same day. Repaired live data alongside their teams while keeping them informed throughout, and fed what they ran into back into the product so the failure could not recur.',
        'Built the entire Shipping Labels system end-to-end, integrating with 5 external APIs including EasyPost, USPS (OAuth2), BukuShip, ShipStation for multi-carrier support (FedEx, UPS, USPS, DHL, Canada Post), and Mapbox for geocoding and route visualization. Implemented PDF generation with pdf-lib, Redis-based caching for rate shopping, webhook management with retry logic, and batch processing capabilities handling 10,000+ label generations daily with sub-2-second average response times and 99.9% uptime.',
      ],
    },
    {
      company: 'Ekarth Ventures',
      about: 'Nahar OM',
      href: 'https://nahar.om',
      place: 'Chennai, India',
      title: 'Full Stack Engineer',
      period: 'July 2024 to March 2025',
      points: [
        'Led frontend development and managed the team delivering Altern8, a real estate lending platform, designing its Next.js and Django architecture for cost efficiency and performance.',
        'Drove CI/CD pipelines on Digital Ocean that cut deployment turnaround by an average of 10 seconds and Docker build size 10-fold (2.2 GB to 178 MB), and managed development and deployment of several third-party B2B APIs for integration with ETHYX Club and the Altern8 platform for data and system interconnectivity.',
        'Pitched and demonstrated the platform to investors internationally.',
      ],
    },
    {
      company: 'DataVerse India',
      href: 'https://dataverseindia.com',
      place: 'Kolkata, India',
      title: 'Full Stack Developer (Intern)',
      period: 'August 2023 to July 2024',
      points: [
        'My first role as an engineer, where I created websites and web applications for various clients and talked to them as a technical spokesperson, learning the fundamentals of full-stack development and getting hands-on experience with cloud hosting platforms like AWS and Hostinger.',
      ],
    },
  ],
  skills: [
    { label: 'Languages', value: 'TypeScript, Swift, Python, Golang' },
    { label: 'Tools', value: 'T3 Code, Claude Code, Zed, Ghostty' },
    { label: 'Frameworks', value: 'Next.js, Django, Express.js, SolidStart, Electron, AppKit, SwiftUI' },
    { label: 'Cloud and databases', value: 'PostgreSQL, MySQL, RDS, S3, EC2, Lambda, Railway, Redis, ClickHouse' },
    { label: 'Books I read', value: 'Algorithms, Network Security, Computer Networks, System Design and Database Optimization' },
    { label: 'Areas of interest', value: 'Web design, serverless architectures, cryptography, typography, low-latency back ends' },
    { label: 'Soft skills', value: 'Product support, product presentation, public speaking, self-learning, adaptability' },
  ],
  education: [
    { course: 'Bachelor of Technology in Electronics and Communication', school: 'Heritage Institute of Technology, Kolkata', grade: 'CGPA 8.21' },
    { course: 'High School', school: 'Ramkrishna Mission Rahara, Kolkata', grade: '91%' },
  ],
}

/** The résumé as a typed letter, plain and a little dry, after Weingart's own. Every fact in it is one oeusume.pdf gives. */
export const resumeLetter: ResumeLetter = {
  sender: ['Anurag Das', 'Product Engineer at Cybership', 'Kolkata, India'],
  place: 'Kolkata',
  recipient: { blank: 'Whoever is reading', address: 'www.anurag.gg/resume' },
  salutation: { anonymous: 'Dear ~~stranger~~ reader,', greeting: 'Dear' },
  body: [
    "People ask what I do, and the short answer never holds up, so here is the long one. I'm a !!Product Engineer!!, three years and a bit, mostly in ==TypeScript, React, Node.js, Python and PostgreSQL==, and I've spent them on 3PL fulfillment and on lending. Since March 2025 I've been at ==Cybership==, remote, on the parts of a fulfillment platform that warehouses lean on.",
    'The ==Automation Rules engine== there is mine, written alone and from scratch, a bit like Shopify Flow, with 50 triggers, 16 condition operators (array ones too) and 7 actions. Zod checks every rule, and they run ==more than 50,000 times a day== across orders, inventory allocation and shipping.',
    "These days it's ==Cybership Desktop==, an Electron app for packing stations that replaces PrintNode. The ~~hard~~ fun part was the scales. They don't say how they talk, so I listened in and ==reverse-engineered most of its 64 scale protocols== from raw serial, USB HID and Bluetooth captures of proprietary scales. The capture tooling ships inside the app. It records the request and response bytes at any serial setting, replays them through the live decoders and sends the evidence to support. The app also ==never prints a label twice==. PostgreSQL row-lock claims, an audited job state machine and an fsynced journal on the device, which repairs torn writes and fails closed, see to that.",
    'I built ==Shipping Labels end to end==. It talks to EasyPost, USPS over OAuth2, BukuShip, and ShipStation for FedEx, UPS, USPS, DHL and Canada Post, finds addresses with Mapbox, draws the PDFs with pdf-lib, caches rate shopping in Redis, and runs webhooks that retry and jobs in batches. ==Over 10,000 labels a day== go through it.',
    "When a warehouse can't ship, it lands on me. I take it ==from the first report to the root cause to a fix that stays fixed==, often the same day, repair the live data with the customer's team, keep them posted, and feed the failure back into the product. Most days I also have ==several agents running at once in T3 Code and Claude Code==, on skills I wrote for them. One reviews a branch against our review contract, and another records video proof of a fix into the PR with Playwright.",
    "Before that, from June 2024 to March 2025, I was at ==Nahar OM== in Chennai, on lending. For ==Secondary Trading== I led a team of 3 and wrote the whole Django REST backend, where investors trade fractional loan units at a fixed price or by bid. It covers OTP and JWT sign-in, Surepass KYC, wallets with an audited transaction log, unit ownership across resales, bidding inside database transactions, eMudhra contracts, a repayment rule engine, a buy-back bot and TDS reports. I wrote an ==XIRR engine== for 4 repayment structures that works a target XIRR back to a price with Brent's method. For Ethyx, their invoice discounting product, I built the ledger and reconciled it against Boost Money account-aggregator bank statements.",
    'On ==Altern8==, construction lending paid out in tranches, I did the frontend and the design. Onboarding can be left and picked up again, and pulls in bank statements through Boost Money, PAN through Signzy, tax returns through Scoreme, and Tally, Zoho or QuickBooks through RootFi. Budgets and timelines upload into editable tables and a Gantt chart, and an admin panel approves borrowers, projects and tranches, each tranche with rules of its own. I got its ==Docker image from 2.2 GB down to 178 MB==, and I ==pitched both products to investors internationally==, walking them through loans split into tradable units, a two-way XIRR calculator, a bid accepted and e-signed, and a borrower taken from onboarding to tranche approval.',
    'From December 2023 to June 2024 I was the ==founding engineer at ProperSKU==, remote, on a Shopify app that forecasts inventory for stores and their warehouses, front to back, in Next.js, TypeScript, GraphQL, Redis and BullMQ. I wrote its ==auth and multi-tenant permissions==. Sign-up is by invite only and cascades across 5 roles (admin, warehouse managers, warehouse users, store owners, store users), each role is fixed by its invite, and the menus and the data are kept to one warehouse or one store. The menu stays locked until onboarding is done, which means setting up the account and card billing (Visa, Mastercard, Amex), connecting Shopify by its domain and inviting the team. It reads Shopify orders, line items, products, variants and inventory per location (available, on hand, committed, backordered), charts sales now and before by product and SKU against other ranges, and ==recommends minimum order quantities== per variant for 3, 6 and 12 months. A warehouse sees every store with its connection status and SKU count, and every account keeps its own billing and its own people.',
    'My first job, from December 2022 to December 2023, was at ==DataVerse India== in Kolkata. I built custom CMS websites from scratch for GenieBaazar and Penn State University in Next.js, SolidStart, Express and Hono, hosted them on AWS and Hostinger, and was the one the clients called.',
    'For the record, I write ==TypeScript, JavaScript, Python, Go, Swift and SQL==. I work in Next.js, React, Node.js, Express.js, Hono, Django, SolidStart, Electron, AppKit and SwiftUI, on PostgreSQL, MySQL, Redis, ClickHouse, AWS (RDS, S3, EC2, Lambda) and Railway. The rest of the toolbox is REST APIs, GraphQL, BullMQ, webhooks, OAuth2, Zod, Docker, CI/CD and production incident response, and multi-agent orchestration with Claude Code, T3 Code and Codex, agent skills and MCP.',
    'I studied ==Electronics and Communication== at Heritage Institute of Technology, Kolkata, and left with a B.Tech and a CGPA of 8.21.',
    "That's most of it. The rest is ==guitar, Arsenal and a cat called Dilly==, which don't fit on a résumé. If any of it is interesting, I'm at sudo@anurag.gg.",
  ],
  closing: 'With many greetings,',
  signature: { src: '/objects/resume/signature.webp', alt: 'Anurag Das', size: [719, 382] },
  enclosures: [
    { label: 'Résumé, PDF', href: '/resume.pdf' },
    { label: 'github.com/oeuvars', href: 'https://github.com/oeuvars' },
    { label: 'linkedin.com/in/oeuvars', href: 'https://www.linkedin.com/in/oeuvars' },
  ],
}
