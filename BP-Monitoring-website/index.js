const express = require("express");
const cors = require("cors");
const { MongoClient, ServerApiVersion, ObjectId } = require("mongodb");
require("dotenv").config();

const app = express();
const port = process.env.PORT || 5000;

app.use(express.json());
app.use(cors({ origin: "*", credentials: true, optionSuccessStatus: 200 }));

// Connect to MongoDB. All credentials and the cluster host come from environment variables.
const uri = `mongodb+srv://${process.env.USER}:${process.env.PASS}@${process.env.MONGO_CLUSTER}/?retryWrites=true&w=majority&appName=Cluster0`;

const client = new MongoClient(uri, {
  serverApi: {
    version: ServerApiVersion.v1,
    strict: true,
    deprecationErrors: true,
  },
});

async function run() {
  try {

    
    const database = client.db("BP_Measuring");
    const ppgCollection = database.collection("rawDataCollection");


    //Insert new PPG record
    app.post("/api/ppgData", async (req, res) => {
      try {
        const { ir, red, spo2, heartRate } = req.body;
        const now = new Date();

        // Find the highest serial number (excluding nulls)
        const lastEntry = await ppgCollection
          .find({ serialNumber: { $ne: null } })
          .sort({ serialNumber: -1 })
          .limit(1)
          .toArray();

        const newSerial = lastEntry.length > 0 ? (lastEntry[0].serialNumber || 0) + 1 : 1;

        const ppgData = {
          serialNumber: newSerial,
          ir,
          red,
          spo2,
          heartRate,
          date: now.toISOString().split("T")[0],
          time: now.toTimeString().split(" ")[0],
          userAge: null,
          userGender: null,
          userHeight: null,
          userWeight: null,
          systolic_BP: null,
          diastolic_BP: null,
        };

        const result = await ppgCollection.insertOne(ppgData);
        res.json({
          message: "PPG data inserted successfully!",
          serialNumber: newSerial,
          insertedId: result.insertedId
        });
        console.log("PPG data inserted successfully!");
      } catch (error) {
        console.error("Error inserting PPG data:", error);
        res.status(500).json({ error: "Failed to insert PPG data." });
      }
    });

    // Fetch the latest data
    app.get("/api/ppgData/latest", async (req, res) => {
      try {

        console.log("Backend: Received request to fetch latest data")

        // Find the latest document (highest serial number)
        const latestDoc = await ppgCollection.find().sort({ serialNumber: -1 }).limit(1).toArray();

        if (!latestDoc.length) {
          console.log("Backend: No data found.");
          return res.status(404).json({ error: "No documents found." });
        }

        // Extract the necessary fields (heartRate, spo2, ir, red)
        const { heartRate, spo2, ir, red } = latestDoc[0];
        console.log("Backend: Returning data -", { heartRate, spo2, ir, red });

        // Return all necessary data (for future prediction use)
        res.json({ heartRate, spo2, ir, red });
      } catch (error) {
        console.error("Error retrieving latest data:", error);
        res.status(500).json({ error: "Failed to retrieve latest data." });
      }
    });



    // Update the latest document
    app.put("/api/ppgData/latest", async (req, res) => {
      try {
        // Log the incoming request body (data to be updated)
        console.log("Backend: Received request to update latest data.");
        console.log("Backend: Request body -", req.body);

        const {
          userAge,
          userGender,
          userHeight,
          userWeight,
          systolic_BP,
          diastolic_BP
        } = req.body;

        // Log extracted data for debugging
        console.log("Backend: Extracted data -", {
          userAge,
          userGender,
          userHeight,
          userWeight,
          systolic_BP,
          diastolic_BP
        });

        // Find the latest document (highest serial number)
        const latestDoc = await ppgCollection.find().sort({ serialNumber: -1 }).limit(1).toArray();
        console.log("Backend: Latest document fetched -", latestDoc);

        if (!latestDoc.length) {
          console.log("Backend: No documents found to update.");
          return res.status(404).json({ error: "No documents found." });
        }

        const latestId = latestDoc[0]._id;
        console.log("Backend: Latest document ID to update -", latestId);

        // Update the latest document with the new values
        const result = await ppgCollection.updateOne(
          { _id: latestId },
          {
            $set: {
              userAge,
              userGender,
              userHeight,
              userWeight,
              systolic_BP,
              diastolic_BP
            }
          }
        );

        // Log the update result
        console.log("Backend: Update result -", result);

        // Check if any documents were modified
        if (result.modifiedCount === 0) {
          console.log("Backend: No modifications made.");
          return res.status(404).json({ error: "No updates made to the document." });
        }

        // Log successful update
        console.log("Backend: Document updated successfully.");
        res.json({
          message: "Latest document updated successfully!",
          modifiedCount: result.modifiedCount
        });
      } catch (error) {
        console.error("Backend: Error occurred while updating document:", error);
        res.status(500).json({ error: "Failed to update." });
      }
    });

    // Update demographics and BP
    app.put("/api/ppgData/:id", async (req, res) => {
      try {
        const id = new ObjectId(req.params.id);
        const {
          userAge,
          userGender,
          userHeight,
          userWeight,
          systolic_BP,
          diastolic_BP,
        } = req.body;

        const result = await ppgCollection.updateOne(
          { _id: id },
          {
            $set: {
              userAge,
              userGender,
              userHeight,
              userWeight,
              systolic_BP,
              diastolic_BP,
            },
          }
        );

        if (result.matchedCount === 0) {
          return res.status(404).json({ error: "Data not found." });
        }

        res.json({ message: "PPG session updated!", modifiedCount: result.modifiedCount });
      } catch (error) {
        console.error("Error updating PPG session:", error);
        res.status(500).json({ error: "Failed to update." });
      }
    });

    //All data
    app.get("/api/ppgData", async (req, res) => {
      try {
        const result = await ppgCollection.find({}).toArray();
        res.send(result);
      } catch (error) {
        console.error("Error retrieving data:", error);
        res.status(500).json({ error: "Failed to retrieve data." });
      }
    });

    // DELETE Delete a record
    app.delete("/api/ppgData/:id", async (req, res) => {
      try {
        const id = new ObjectId(req.params.id);
        const result = await ppgCollection.deleteOne({ _id: id });
        if (result.deletedCount === 0) {
          return res.status(404).json({ error: "Data not found." });
        }
        res.json({ message: "Deleted successfully!" });
      } catch (error) {
        console.error("Error deleting data:", error);
        res.status(500).json({ error: "Failed to delete." });
      }
    });

    

    await client.db("admin").command({ ping: 1 });
    console.log("MongoDB connected!");
  } catch (err) {
    console.error("MongoDB connection failed:", err);
  }
}

run().catch(console.dir);


// Home endpoint
app.get("/", (req, res) => {
  res.send({ message: "Welcome to the PPG BP API", status: "OK" });
});


// Start server
app.listen(port, () => {
  console.log(`Server is running at http://localhost:${port}`);
});
