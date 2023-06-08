import LineGradient from "../components/LineGradient";
import useMediaQuery from "../hooks/useMediaQuery";
import { motion } from "framer-motion";
import skill from "../assets/Images/artskills.webp";

const MySkills = () => {
  const isAboveLarge = useMediaQuery("(min-width: 1060px)");
  return (
    <section id="skills" className="pt-1 mb-16">

      {/* HEADER AND IMAGE SECTION */}

      <div className="md:flex md:justify-between md:gap-16">
        <motion.div
          className="md:w-1/2 -mt-10"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.5 }}
          transition={{ duration: 0.5 }}
          variants={{
            hidden: { opacity: 0, x: -50 },
            visible: { opacity: 1, x: 0 },
          }}
        >
          <p className="font-playfair font-semibold text-3xl md:text-4xl text-deep-blue mb-5">
            THE <span className="text-bloodred">SKILLS</span>
          </p>
          <LineGradient width="w-2/3" />
          <p className="mt-8 mb-7 text-black font-outfit font-medium phone:text-sm lg:text-base">
            I possess exceptional skills in web development and designing, creating visually stunning and functional websites with a seamless user experience.
          </p>
        </motion.div>

        <div className="mt-16 md:mt-0">
          {isAboveLarge ? (
            <div
              className="flex relative z-0 ml-96 before:absolute before:-top-10 before:-left-10
              before:w-full before:h-full before:border-2 before:border-bronze before:z-[-1]"
            >
              <img
                alt="skills"
                className="flex ml-36 z-10 h-1/6 w-1/2"
                src={skill}
              />
            </div>
          ) : (
            <div
            className="flex relative z-0 ml-12 before:absolute before:-top-5 before:-left-5
            before:w-4/5 before:h-5/6 before:border-2 before:border-bronze before:z-[-1]"
            >
              <img alt="skills" className="flex ml-1 z-10 scale-90" src={skill} />
            </div>
          )}
        </div>
      </div>

      {/* SKILLS */}
      <div className="md:flex md:justify-between mt-16 gap-32">
        {/* EXPERIENCE */}
        <motion.div
          className="md:w-1/3 mt-16"
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.5 }}
          transition={{ duration: 0.5 }}
          variants={{
            hidden: { opacity: 0, y: 50 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <div className="relative h-32">
            <div className="z-10 flex flex-col my-auto justify-center">
              <p className="font-playfair text-black font-semibold text-5xl">01</p>
              <p className="font-playfair text-brown-red font-semibold text-3xl mt-3">
                Front-End
              </p>
            </div>
            <div className="w-1/2 md:w-3/4 h-32 bg-gradient-to-r from-yellow-200 via-pink-200 to-pink-400 saturate-150 rounded-lg opacity-30 drop-shadow-2xl absolute right-0 top-0 lg:z-[-1]" ></div>
          </div>
          <p className="phone:text-sm lg:text-base mt-5 font-outfit font-medium text-base text-jet">
            With a keen eye for design and a knack for problem-solving, my web development skills bring ideas to life through seamless functionality and stunning aesthetics.
          </p>
        </motion.div>

          {/* INNOVATIVE */}
          <motion.div
            className="md:w-1/3 mt-16"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.5 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            variants={{
              hidden: { opacity: 0, y: 50 },
              visible: { opacity: 1, y: 0 },
            }}
          >
            <div className="relative h-32">
              <div className="z-10 flex flex-col my-auto justify-center">
                <p className="font-playfair font-semibold text-black text-5xl">02</p>
                <p className="font-playfair text-brown-red font-semibold text-3xl mt-3">
                  Designing
                </p>
              </div>
              <div className="w-1/2 md:w-3/4 h-32 bg-gradient-to-r from-red-200 via-red-300 to-yellow-200 saturate-200 rounded-lg opacity-30 drop-shadow-2xl absolute right-0 top-0 lg:z-[-1]" ></div>
            </div>
            <p className="mt-5 font-outfit font-medium text-base text-jet phone:text-sm lg:text-base">
              My design skills blend creativity and attention to detail, resulting in visually captivating graphics and layouts that effectively communicate messages and captivate audiences.
            </p>
          </motion.div>
          {/* IMAGINATIVE */}
          <motion.div
            className="md:w-1/3 mt-16"
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.5 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            variants={{
              hidden: { opacity: 0, y: 50 },
              visible: { opacity: 1, y: 0 },
            }}
          >
            <div className="relative h-32">
              <div className="z-10 flex flex-col my-auto justify-center">
                <p className="font-playfair font-semibold text-black text-5xl">03</p>
                <p className="font-playfair font-semibold text-brown-red text-3xl mt-3">
                  Back-End
                </p>
              </div>
              <div className="w-1/2 md:w-3/4 h-32 bg-gradient-to-r from-yellow-100 via-yellow-300 to-yellow-500 rounded-lg opacity-40 drop-shadow-2xl absolute right-0 top-0 lg:z-[-1]" >

              </div>
            </div>
            <p className="mt-5 font-outfit font-medium text-base text-jet phone:text-sm lg:text-base">
              As a backend web developer, I excel at building robust and scalable systems, optimizing performance, and ensuring seamless data management for efficient web applications.
            </p>
          </motion.div>
      </div>

    </section>
  );
};

export default MySkills;
