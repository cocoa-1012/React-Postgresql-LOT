import { Alert, AlertIcon, Button, ButtonGroup, Heading, VStack } from "@chakra-ui/react";
import { Form, Formik } from "formik";
import { useNavigate } from "react-router";
import { useContext, useState } from "react";
import { AccountContext } from "../AccountContext";
import * as Yup from "yup";
import TextField from "../TextField";

const Login = () => {
  const { setUser } = useContext(AccountContext);
  const [error, setError] = useState(null);
  const [showError, setShowError] = useState(false);
  const navigate = useNavigate();
  return (
    <>
      <Formik
        initialValues={{ username: "", password: "" }}
        validationSchema={Yup.object({
          username: Yup.string()
            .required("Username required!")
            .min(6, "Username too short!"),
          password: Yup.string()
            .required("Password required!")
            .min(6, "Password too short!"),
        })}
      
        onSubmit={(values, actions) => {
          const vals = { ...values };
          actions.resetForm();
          fetch("http://localhost:4000/auth/login", {
            method: "POST",
            credentials: "include",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(vals),
          })
            .catch(err => {
              return;
            })
            .then(res => {
              if (!res || !res.ok || res.status >= 400) {
                return;
              }
              return res.json();
            })
            .then(data => {
              if (!data) return;
              setUser({ ...data });
              if (data.status) {
                setError(data.status);
                setShowError(true);
              } else if (data.loggedIn) {
                navigate("/home");
              }
            });
        }}
      >
        <VStack
          as={Form}
          w={{ base: "90%", md: "500px" }}
          m="auto"
          justify="center"
          h="100vh"
          spacing="1rem"
        >
          <Heading>Log In</Heading>
          <TextField
            name="username"
            placeholder="Enter username"
            autoComplete="off"
            label="Username"
          />

          <TextField
            name="password"
            placeholder="Enter password"
            autoComplete="off"
            label="Password"
            type="password"
          />

          <ButtonGroup pt="1rem">
            <Button colorScheme="teal" type="submit">
              Log In
            </Button>
            <Button onClick={() => navigate("/register")}>Create Account</Button>
          </ButtonGroup>
        </VStack>
      </Formik>
      { showError 
      ? (<Alert status='error'>
          <AlertIcon />
          {error}
        </Alert>
      ) : null
      }
    </>
  );
};

export default Login;