import LineGradient from "../components/LineGradient";
import { useForm } from "react-hook-form";
import { motion } from "framer-motion";
import contact from "../assets/contact.webp";
import useMediaQuery from "../hooks/useMediaQuery";

const Contact = () => {
  const {
    register,
    trigger,
    formState: { errors },
  } = useForm();

  const onSubmit = async (e) => {
    console.log("~ e", e);
    const isValid = await trigger();
    if (!isValid) {
      e.preventDefault();
    }
  };
  const isAboveSmallScreens = useMediaQuery("(min-width: 768px)");

  return (
    <section id="contact" className={`contact phone:pt-80 phone:mt-5 md:pt-0 tablet:pt-0 sm:pt-0 lg:pt-7`}>
      {/* HEADINGS */}
      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.5 }}
        transition={{ duration: 0.5 }}
        variants={{
          hidden: { opacity: 0, x: 50 },
          visible: { opacity: 1, x: 0 },
        }}
        className={`flex ${isAboveSmallScreens? 'justify-end' : 'justify-center'} w-full`}
      >
        <div>
          <p className="font-playfair font-semibold text-3xl md:text-4xl text-black">
            <span className="text-bl text-black">CONTACT </span> ME
          </p>
          <div className="flex my-5">
            <LineGradient width="w-1/2" />
          </div>
        </div>
      </motion.div>

      {/* FORM & IMAGE */}
      <div className="md:flex md:justify-between gap-16 mt-5">
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.5 }}
          transition={{ duration: 0.5 }}
          variants={{
            hidden: { opacity: 0, y: 50 },
            visible: { opacity: 1, y: 0 },
          }}
          className="basis-1/2 flex flex-col justify-center"
        >
          <img className="rounded-xl shadow-md" src={contact} alt="contact" />
          <motion.p className="text-jet font-outfit lg:font-playfair font-semibold mt-5 text-sm lg:text-xl phone:text-base text-center overflow-x-visible">Me and my pals up here would love to talk to</motion.p>
          <motion.p className="text-brown-red text-xl lg:text-3xl font-playfair font-semibold py-2 text-center">YOU</motion.p>
        </motion.div>

        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.5 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          variants={{
            hidden: { opacity: 0, y: 50 },
            visible: { opacity: 1, y: 0 },
          }}
          className="basis-1/2 mt-10 md:mt-0 phone:mb-8 lg:mb-16
          "
        >
          <form
            target="_blank"
            onSubmit={onSubmit}
            action="https://getform.io/f/5ccdf2d3-0c3e-4e5d-9273-32fa5950cec7"
            method="POST"
          >
            <input
              className="w-full bg-eggshell text-jet rounded-xl shadow-lg font-montserrat font-semibold placeholder-opaque-black p-3"
              type="text"
              placeholder="NAME"
              {...register("name", {
                required: true,
                maxLength: 100,
              })}
            />
            {errors.name && (
              <motion.p className="text-greensheen mt-1 font-montserrat text-sm font-medium">
                {errors.name.type === "required" && "This field is required."}
                {errors.name.type === "maxLength" && "Max length is 100 char."}
              </motion.p>
            )}

            <input
              className="w-full bg-eggshell text-jet rounded-xl shadow-lg font-montserrat font-semibold placeholder-opaque-black p-3 mt-5"
              type="text"
              placeholder="EMAIL"
              {...register("email", {
                required: true,
                pattern: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
              })}
            />
            {errors.email && (
              <p className="text-greensheen mt-1 font-montserrat text-sm font-medium">
                {errors.email.type === "required" && "This field is required."}
                {errors.email.type === "pattern" && "Invalid email address."}
              </p>
            )}

            <textarea
              className="w-full bg-eggshell text-jet rounded-xl shadow-lg font-montserrat font-semibold placeholder-opaque-black p-3 mt-5"
              name="message"
              placeholder="MESSAGE"
              rows="4"
              cols="50"
              {...register("message", {
                required: true,
                maxLength: 2000,
              })}
            />
            {errors.message && (
              <p className="text-greensheen mt-1 font-montserrat text-sm font-medium">
                {errors.message.type === "required" &&
                  "This field is required."}
                {errors.message.type === "maxLength" &&
                  "Max length is 2000 char."}
              </p>
            )}

            <button
              className="flex lg:mx-0 phone:mx-auto phone:px-4 lg:px-7 py-3 bg-black bg-opacity-90 font-montserrat font-semibold text-white mt-5 hover:bg-stone-800 hover:text-cosmicwhite transition duration-500"
              type="submit"
            >
              Submit
            </button>
          </form>
        </motion.div>
      </div>
      <p className="text-jet text-center font-semibold text-sm phone:pb-2 lg:pb-5 font-montserrat lg:pt-10">© Anurag Das 2023</p>
    </section>
  );
};

export default Contact;
