import type { Chat, Cv, PageId, PageMeta, Profile, Site } from './types'

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
    description: "My résumé, as a text thread with me: Cybership since March 2025, Ekarth Ventures and DataVerse India before that, and what I do when I'm not working. Type a message and it opens in Gmail.",
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
        'Pitched and demonstrated the platform to investors across the US, Turkey, Netherlands and India.',
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
    { label: 'Books I read', value: 'Algorithms, Network Security, Computer Networks, System Design and Database Optimization' },
    { label: 'Areas of interest', value: 'Web design, serverless architectures, cryptography, typography, low-latency back ends' },
    { label: 'Soft skills', value: 'Product support, product presentation, public speaking, self-learning, adaptability' },
  ],
  education: [
    { course: 'Bachelor of Technology in Electronics and Communication', school: 'Heritage Institute of Technology, Kolkata', grade: 'CGPA 8.21' },
    { course: 'High School', school: 'Ramkrishna Mission Rahara, Kolkata', grade: '91%' },
  ],
}

/** The résumé as a text conversation, every figure in it one resume.pdf gives. The reader's side asks the questions. */
export const chat: Chat = {
  contact: { name: 'Anurag', avatar: '/objects/resume/avatar.avif' },
  thread: [
    { side: 'me', kind: 'text', text: "Hey, I'm Anurag" },
    { side: 'me', kind: 'photo', src: '/photos/face.jpg', alt: 'Me, with curly hair and a maroon shirt, against a dark teal wall.', size: [1000, 1000] },
    { side: 'me', kind: 'text', text: "I'm a product engineer at Cybership. I build the servers and the screens behind a fulfillment platform for warehouses" },
    { side: 'you', kind: 'text', text: 'What does that look like day to day?' },
    { side: 'me', kind: 'text', text: "I've been there since March 2025, working remote" },
    { side: 'me', kind: 'link', href: 'https://cybership.io', title: 'Cybership', icon: '/objects/resume/cybership.webp' },
    { side: 'me', kind: 'text', text: 'I built their automation rules from scratch, so a merchant can say "when this happens, do that" and stop doing it by hand. They run over 50,000 times a day now' },
    { side: 'me', kind: 'text', text: "I also made the desktop app that runs at the packing stations. It prints the labels and reads the scales" },
    { side: 'me', kind: 'text', text: 'And the shipping labels themselves. More than 10,000 a day, usually in under two seconds each' },
    { side: 'me', kind: 'text', text: "When a warehouse can't ship, that's mine to fix, and I stay on it until it's fixed for good. Often the same day" },
    { side: 'you', kind: 'text', text: 'And before Cybership?' },
    { side: 'me', kind: 'text', text: 'Ekarth Ventures, in Chennai, for about eight months. I led the frontend team on Altern8, a real estate lending platform' },
    { side: 'me', kind: 'link', href: 'https://nahar.om', title: 'Ekarth Ventures', icon: '/objects/resume/ekarth.webp' },
    { side: 'me', kind: 'text', text: 'I also ended up pitching it to investors in the US, Turkey, the Netherlands and India' },
    { side: 'me', kind: 'text', text: 'Before that I interned at DataVerse India' },
    { side: 'you', kind: 'text', text: 'What do you like working with?' },
    { side: 'me', kind: 'text', text: 'Mostly TypeScript, with some Swift, Python and Go' },
    { side: 'me', kind: 'text', text: "And I'm picky about fonts, which you might have noticed" },
    { side: 'you', kind: 'text', text: 'Where did you study?' },
    { side: 'me', kind: 'text', text: 'Electronics and Communication at Heritage Institute of Technology. I finished with an 8.21' },
    { side: 'you', kind: 'text', text: 'And outside work?' },
    { side: 'me', kind: 'text', text: 'Electric guitar, mostly' },
    { side: 'me', kind: 'text', text: 'I love football, Arsenal to be precise' },
    { side: 'me', kind: 'text', text: 'And Dilly, my cat, who likes to fall asleep on my keyboard' },
    { side: 'you', kind: 'text', text: 'Can I get your résumé as a PDF?' },
    { side: 'me', kind: 'text', text: 'Here you go' },
    { side: 'me', kind: 'file', href: '/resume.pdf', name: 'Anurag Das, résumé.pdf', detail: 'PDF Document · 33 KB' },
  ],
  subject: 'Hi Anurag',
  reply: "Gmail should be open now. Hit send there and I'll get it",
  placeholder: 'iMessage',
}
